// Supabase Edge Function: generate tailored resume + cover letter.
// Replaces the former Netlify function (which hit Netlify's ~26s sync timeout —
// this runtime allows far longer, fixing the 504s).
//
// POST { title, company, description, why, location }
//   -> { resume, cover_letter, application_id }
//
// Reads the candidate's resume.md + job_profile.json from Supabase Storage,
// calls the OpenRouter LLM to tailor them to the role, and persists the results
// into the application_documents table (job resolved/created by title+company).
// Runs with SERVICE ROLE privileges because the platform injects
// SUPABASE_SERVICE_ROLE_KEY / SUPABASE_URL into this runtime server-side.

// --- CORS ---------------------------------------------------------------
const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
};

function corsResponse(status, body) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...corsHeaders, "Content-Type": "application/json" },
  });
}

// --- LLM call (raw fetch, no SDK) --------------------------------------
async function callLLM(messages) {
  const key = Deno.env.get("OPENROUTER_API_KEY") || Deno.env.get("OPENAI_API_KEY");
  if (!key) return { error: "OPENROUTER_API_KEY not configured on this function" };

  const url = "https://openrouter.ai/api/v1/chat/completions";
  const model = Deno.env.get("LLM_MODEL") || "deepseek/deepseek-v4-flash-0731";

  try {
    const resp = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${key}` },
      body: JSON.stringify({ model, messages, temperature: 0.4, max_tokens: 4000 }),
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

// --- Storage-supplied source files (one-time provisioned) --------------
const SUPABASE_URL = (Deno.env.get("SUPABASE_URL") || "").replace(/\/+$/, "");
const SERVICE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") || Deno.env.get("SUPABASE_SERVICE_KEY") || "";
const BUCKET = Deno.env.get("SUPABASE_BUCKET") || "candidate";

// Make a Supabase PostgREST / Storage request with the service role.
function sbAuth() {
  return {
    apikey: SERVICE_KEY,
    Authorization: `Bearer ${SERVICE_KEY}`,
    "Content-Type": "application/json",
  };
}

async function fetchSourceFromStorage(name) {
  const url = `${SUPABASE_URL}/storage/v1/object/${encodeURIComponent(BUCKET)}/${name}`;
  const resp = await fetch(url, {
    headers: { apikey: SERVICE_KEY, Authorization: `Bearer ${SERVICE_KEY}` },
  });
  if (!resp.ok) throw new Error(`storage ${BUCKET}/${name}: HTTP ${resp.status}`);
  return resp.text();
}

// Read the candidate's master resume + profile. Optional — the prompt tolerates
// a missing one (LLM just has less context).
async function fetchSource(name) {
  try {
    return await fetchSourceFromStorage(name);
  } catch (e) {
    console.warn(`[generate] could not read ${name} from storage: ${e.message}`);
    return "";
  }
}

// --- Persistence --------------------------------------------------------
function slugify(s) {
  return (
    (s || "").toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "").slice(0, 80) || "untitled"
  );
}

// Reuse an existing jobs row by (title, company), else create one with a stable
// derived canonical_url so regenerations upsert rather than duplicate.
async function resolveJobId(job) {
  const q = new URLSearchParams({
    select: "id,title,company",
    title: `eq.${job.title}`,
    company: `eq.${job.company}`,
    limit: "1",
  });
  const found = await fetch(`${SUPABASE_URL}/rest/v1/jobs?${q}`, { headers: sbAuth() });
  if (found.ok) {
    const rows = await found.json();
    if (rows?.[0]?.id) return rows[0].id;
  }

  const canonical_url = `generated://${slugify(job.company)}/${slugify(job.title)}`;
  const created = await fetch(`${SUPABASE_URL}/rest/v1/jobs?on_conflict=canonical_url`, {
    method: "POST",
    headers: { ...sbAuth(), Prefer: "resolution=merge-duplicates,return=representation" },
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
  });
  if (!created.ok) throw new Error(`upsert job: HTTP ${created.status}`);
  const rows = await created.json();
  return rows?.[0]?.id;
}

async function upsertDocument(jobId, type, content, model) {
  const resp = await fetch(
    `${SUPABASE_URL}/rest/v1/application_documents?on_conflict=job_id,user_id,document_type,format`,
    {
      method: "POST",
      headers: { ...sbAuth(), Prefer: "resolution=merge-duplicates,return=representation" },
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

async function persistApplication(jobData, resumeMd, coverMd, model) {
  if (!SUPABASE_URL || !SERVICE_KEY) return null;
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

// --- Handler ------------------------------------------------------------
Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: corsHeaders });

  let job;
  try {
    job = await req.json();
  } catch {
    return corsResponse(400, { error: "invalid JSON" });
  }

  const title = job.title || "";
  const company = job.company || "";
  const description = (job.description || "").slice(0, 1200);
  const why = job.why || "";
  const location = job.location || "";

  const resume = await fetchSource("resume.md");
  const profile = await fetchSource("job_profile.json");

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
    return corsResponse(502, {
      error: result.error,
      hint: "Ensure OPENROUTER_API_KEY secret is set on this Supabase function.",
    });
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
    result.model || Deno.env.get("LLM_MODEL") || "deepseek/deepseek-v4-flash-0731",
  );

  return corsResponse(200, { resume: resumeMd, cover_letter: coverMd, application_id: applicationId });
});