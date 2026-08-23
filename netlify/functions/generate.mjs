// netlify/functions/generate.mjs
// Serverless handler powering the "✨ Generate" button on each dashboard card.
//
// Contract (see index.html -> window.generateJob):
//   POST /.netlify/functions/generate
//   body:  { title, company, description, why, location }
//   resp:  { resume: "<markdown>", cover_letter: "<markdown>" }
//
// The client renders the returned markdown to styled HTML and invokes the
// browser print dialog to produce the PDF. No server-side PDF needed.
//
// Secrets are read from Netlify env vars (set via `netlify env:set`), NOT from
// committed source. Reads: OPENROUTER_API_KEY (or OPENAI_API_KEY) and LLM_MODEL.
// Default model: DeepSeek V4 Flash on OpenRouter.

// --- LLM call via raw fetch (no SDK dependency) --------------------------
async function callLLM(messages) {
  const key = process.env.OPENROUTER_API_KEY || process.env.OPENAI_API_KEY;
  if (!key) {
    return { error: "OPENROUTER_API_KEY not configured on this function" };
  }

  const url = "https://openrouter.ai/api/v1/chat/completions";
  const model = process.env.LLM_MODEL || "deepseek/deepseek-v4-flash-0731";

  try {
    const resp = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${key}`,
      },
      body: JSON.stringify({
        model,
        messages,
        temperature: 0.4,
        max_tokens: 4000,
      }),
    });

    if (!resp.ok) {
      const body = await resp.text();
      return { error: `LLM upstream ${resp.status}: ${body.slice(0, 300)}` };
    }
    const data = await resp.json();
    const content = data?.choices?.[0]?.message?.content;
    if (!content) return { error: "LLM returned empty content" };
    return { content, model };
  } catch (e) {
    return { error: `fetch failed: ${e.message}` };
  }
}

// --- Source files (resume.md / job_profile.json) ----------------------------
// Preferred: read from Supabase Storage ({SUPABASE_URL}/storage/v1/object/...).
// The commit-to-repo + origin-fetch approach below is the legacy fallback and
// will be removed once the Storage migration is verified.
//
// One-time provisioning (run once, then the env vars below do the rest):
//
//   # 1. Create the bucket (SQL Editor):
//   insert into storage.buckets (id, name, public) values ('candidate', 'candidate', false);
//
//   # 2. Upload the two source files (Storage > candidate > Upload):
//   #      candidate/resume.md
//   #      candidate/job_profile.json
//
// Environment (Netlify -> Site config -> Environment variables):
//   SUPABASE_URL=https://<project>.supabase.co
//   SUPABASE_SERVICE_KEY=<service_role key>
//   SUPABASE_BUCKET=candidate   (defaults to "candidate")
const SUPABASE_URL = (process.env.SUPABASE_URL || "").replace(/\/+$/, "");
const SUPABASE_KEY =
  process.env.SUPABASE_SERVICE_KEY || process.env.SUPABASE_ANON_KEY || "";
const SUPABASE_BUCKET = process.env.SUPABASE_BUCKET || "candidate";

// Read a file from Supabase Storage. Throws on error (caller decides fallback).
async function fetchSourceFromStorage(name) {
  if (!SUPABASE_URL || !SUPABASE_KEY) {
    throw new Error("SUPABASE_URL/SUPABASE_SERVICE_KEY not configured");
  }
  const url = `${SUPABASE_URL}/storage/v1/object/${encodeURIComponent(SUPABASE_BUCKET)}/${name}`;
  const resp = await fetch(url, {
    headers: {
      apikey: SUPABASE_KEY,
      Authorization: `Bearer ${SUPABASE_KEY}`,
    },
    signal: AbortSignal.timeout(10000),
  });
  if (!resp.ok) throw new Error(`storage ${SUPABASE_BUCKET}/${name}: HTTP ${resp.status}`);
  return resp.text();
}

// Legacy: fetch a committed repo-root file from the deployed site origin.
// Kept so the function still works while the Supabase Storage migration is in
// flight. NOTE: Netlify's SPA catch-all will return index.html (HTTP 200) for
// a missing file, which is why the Storage path is preferred — it fails loudly.
async function fetchSourceFromOrigin(event, name) {
  const host = event?.headers?.["host"] || event?.headers?.["x-forwarded-host"];
  const proto =
    event?.headers?.["x-forwarded-proto"] ||
    event?.headers?.["x-forwarded-protocol"] ||
    "https";
  const origin = host ? `${proto}://${host}` : "https://job-dashboard-sam.netlify.app";
  const resp = await fetch(`${origin}/${name}`, { signal: AbortSignal.timeout(10000) });
  if (!resp.ok) throw new Error(`${name}: HTTP ${resp.status}`);
  return resp.text();
}

// Try Storage first, then the legacy origin fetch. Never throws — callers
// should tolerate an empty string (the LLM prompt handles missing context).
async function fetchSourceFile(event, name) {
  try {
    return await fetchSourceFromStorage(name);
  } catch (e) {
    console.warn(`[generate] Supabase fetch ${name} failed (${e.message}); falling back to origin`);
  }
  try {
    return await fetchSourceFromOrigin(event, name);
  } catch (e) {
    console.warn(`[generate] origin fetch ${name} failed: ${e.message}`);
  }
  return "";
}

// --- Persistence (saved-applications library) ----------------------------
// The "✨ Generate" buttons don't send a job id, only title/company/etc. To store
// documents against the schema's UNIQUE(job_id, user_id, document_type, format)
// constraint we resolve an existing jobs row by (title, company) or create one,
// then upsert the resume + cover_letter. Uses the service key (bypasses RLS,
// same role as the n8n pipeline). Failures are logged, not fatal: we still
// return the generated docs to the browser even if persisting is unavailable.

function slugify(s) {
  return (
    (s || "")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/^_+|_+$/g, "")
      .slice(0, 80) || "untitled"
  );
}

function supabaseHeaders() {
  return {
    apikey: SUPABASE_KEY,
    Authorization: `Bearer ${SUPABASE_KEY}`,
    "Content-Type": "application/json",
  };
}

// Reuse an existing jobs row by (title, company); otherwise create one with a
// stable derived canonical_url so regenerations upsert rather than duplicate.
async function resolveJobId(job) {
  const q = new URLSearchParams({
    select: "id,title,company",
    title: `eq.${job.title}`,
    company: `eq.${job.company}`,
    limit: "1",
  });
  const found = await fetch(`${SUPABASE_URL}/rest/v1/jobs?${q}`, {
    headers: supabaseHeaders(),
  });
  if (found.ok) {
    const rows = await found.json();
    if (rows?.[0]?.id) return rows[0].id;
  }

  const canonical_url = `generated://${slugify(job.company)}/${slugify(job.title)}`;
  const created = await fetch(
    `${SUPABASE_URL}/rest/v1/jobs?on_conflict=canonical_url`,
    {
      method: "POST",
      headers: {
        ...supabaseHeaders(),
        Prefer: "resolution=merge-duplicates,return=representation",
      },
      body: JSON.stringify({
        canonical_url,
        source: "generated",
        application_route_type: "On-demand (dashboard): generate",
        listing_verification: "Generated from verified candidate profile",
        title: job.title,
        company: job.company,
        location: job.location || "Melbourne",
        description: (job.description || "").slice(0, 1200),
      }),
    },
  );
  if (!created.ok) throw new Error(`upsert job: HTTP ${created.status}`);
  const createdRows = await created.json();
  return createdRows?.[0]?.id;
}

async function upsertDocument(jobId, type, content, model) {
  const resp = await fetch(
    `${SUPABASE_URL}/rest/v1/application_documents?on_conflict=job_id,user_id,document_type,format`,
    {
      method: "POST",
      headers: {
        ...supabaseHeaders(),
        Prefer: "resolution=merge-duplicates,return=representation",
      },
      body: JSON.stringify({
        job_id: jobId,
        user_id: null,
        document_type: type,
        format: "markdown",
        content,
        source_model: model,
        is_draft: false,
      }),
    },
  );
  if (!resp.ok) {
    const body = await resp.text();
    throw new Error(`document ${type} upsert: HTTP ${resp.status}: ${body.slice(0, 200)}`);
  }
}

// Persist a generated application. Returns the jobs row id, or null if Supabase
// is unavailable / the write fails (callers keep the docs either way).
async function persistApplication(jobData, resumeMd, coverMd, model) {
  if (!SUPABASE_URL || !SUPABASE_KEY) return null;
  try {
    const jobId = await resolveJobId(jobData);
    if (resumeMd) await upsertDocument(jobId, "resume", resumeMd, model);
    if (coverMd) await upsertDocument(jobId, "cover_letter", coverMd, model);
    return jobId;
  } catch (e) {
    console.warn(`[generate] persist skipped: ${e.message}`);
    return null;
  }
}

export const handler = async (event) => {
  let job;
  try {
    job = JSON.parse(event.body || "{}");
  } catch {
    return { statusCode: 400, body: JSON.stringify({ error: "invalid JSON" }) };
  }

  const title = job.title || "";
  const company = job.company || "";
  const description = (job.description || "").slice(0, 1200);
  const why = job.why || "";
  const location = job.location || "";

  // Candidate source-of-truth. Prefers Supabase Storage, falls back to the
  // origin fetch. Returns "" if both are unavailable (prompt still works, just
  // with less context).
  const resume = await fetchSourceFile(event, "resume.md");
  const profile = await fetchSourceFile(event, "job_profile.json");

  const systemPrompt = `You are a senior Australian recruitment specialist producing a
tailored résumé and cover letter, in Markdown, from the candidate's REAL, VERIFIED
work history ONLY.

RULES — ABSOLUTE:
- NEVER fabricate employers, job titles, dates, qualifications, licences, security
  clearances, vehicle access, RSA, or any skill not present in the candidate profile.
- The role-specific résumé should re-order and tailor REAL experience and skills to
  match the job posting.
- Cover letter: 3-4 short paragraphs, professional but human, referencing the company,
  role title, location, and 2-3 genuinely matched wins. No fabrications.
- Australian spelling (organise, licence). Clean Markdown.
- Do NOT include an email/phone identity block at the top of the résumé body; the
  on-screen header already carries the identity.`;

  const userPrompt = `Candidate master résumé (VERIFIED FACT ONLY):
${resume}

Candidate profile JSON:
${profile}

=== TARGET ROLE ===
Title: ${title}
Company: ${company}
Location: ${location}
Why we flagged it: ${why}

Role description:
${description}

Produce TWO Markdown documents, separated exactly by the single line:
===COVER_LETTER===

Résumé section first (## Résumé headings, - bullets, no identity/contact block),
then the separator line, then the cover letter (## Cover Letter, 3-4 paragraphs,
company-aware).`;

  const result = await callLLM([
    { role: "system", content: systemPrompt },
    { role: "user", content: userPrompt },
  ]);

  if (result.error) {
    return {
      statusCode: 502,
      body: JSON.stringify({
        error: result.error,
        hint: "Ensure OPENROUTER_API_KEY env is set on this Netlify function.",
      }),
    };
  }

  const SEP = "===COVER_LETTER===";
  const idx = result.content.indexOf(SEP);
  let resumeMd = result.content;
  let coverMd = "";
  if (idx >= 0) {
    resumeMd = result.content.slice(0, idx).trim();
    coverMd = result.content.slice(idx + SEP.length).trim();
  }

  // Persist to Supabase so the saved-applications library can list them later.
  const applicationId = await persistApplication(
    { title, company, location, description: job.description || "" },
    resumeMd,
    coverMd,
    result.model || process.env.LLM_MODEL || "deepseek/deepseek-v4-flash-0731"
  );

  return {
    statusCode: 200,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ resume: resumeMd, cover_letter: coverMd, application_id: applicationId }),
  };
};