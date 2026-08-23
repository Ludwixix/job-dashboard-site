// Supabase Edge Function: async generation worker (queue drainer).
//
// This is the replacement for the old ~2min synchronous Generate body. It is
// invoked on an interval — by pg_cron+pg_net (preferred, see supabase/pg_cron/)
// or by a free GitHub Actions cron fallback (.github/workflows/worker-cron.yml).
//
// Each warm invocation:
//   1. Claims the OLDEST generation_jobs row with status='queued' and marks it
//      'running' (atomically-ish via the attempt flag; safely re-entrant — if
//      none is found it returns { processed: 0 } immediately).
//   2. Reads resume.md + job_profile.json from Storage bucket "candidate".
//   3. Calls OpenRouter (deepseek/deepseek-v4-flash-0731, temp 0.4, 4000 tok)
//      with the SAME system/user prompts as the old synchronous generator.
//   4. Splits on the exact line "===COVER_LETTER===" into resume/cover markdown.
//   5. Persists via service role + LOCAL_USER_ID into jobs + application_documents
//      (same shape as before, so the untouched /applications list still works).
//   6. Flips the generation_jobs row to 'completed' (+ completed_at + application_id)
//      or 'error' (+ error message) on any failure.
//
// Because the cron fires every ~30s and this function returns quickly when the
// queue is empty, this is effectively free on Supabase's free plan.

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

// Local dashboard "user" for generated documents. The dashboard has no auth,
// so documents are attributed to this fixed user. A real UUID keeps the
// UNIQUE(job_id, user_id, document_type, format) constraint working, so
// regenerating the same role merges instead of duplicating rows.
const LOCAL_USER_ID = "00000000-0000-4000-8000-000000000001";

// Make a Supabase PostgREST / Storage request with the service role.
function sbAuth() {
  return {
    apikey: SERVICE_KEY,
    Authorization: `Bearer ${SERVICE_KEY}`,
    "Content-Type": "application/json",
  };
}

// Read the candidate's master resume + profile. Optional — the prompt tolerates
// a missing one (LLM just has less context).
// Source-of-truth fetcher.
//
// The candidate's canonical record + generation guidelines live in the repo
// and are published to raw.githubusercontent.com (public, no auth). The worker
// pulls them from there instead of Storage so the source-of-truth is a single
// tracked source (no Storage upload needed). Falls back to the legacy resume.md
// if the curated Master Resume isn't reachable.
const SOURCE_BASE = "https://raw.githubusercontent.com/Ludwixix/job-dashboard-site/master/";

// Map the logical source names the worker asks for to public repo paths.
// Explicitly URL-encoded because paths contain spaces ("Source of truth/Master Resume.md").
const SOURCE_PATHS = {
  "master-resume.md": "Source%20of%20truth/Master%20Resume.md",
  "resume.md": "Source%20of%20truth/resume.md",
  "job_profile.json": "job_profile.json",
  "agent_prompt.md": "Guidelines/Resume%20%26%20Cover%20Letter%20Generation%20%E2%80%94%20Combined%20Agent%20Prompt.md",
};

async function fetchSource(name) {
  const path = SOURCE_PATHS[name];
  if (!path) return "";
  const url = SOURCE_BASE + path;
  try {
    const resp = await fetch(url, {
      headers: { Accept: "text/plain, application/json" },
    });
    if (!resp.ok) throw new Error(`source ${url}: HTTP ${resp.status}`);
    return await resp.text();
  } catch (e) {
    console.warn(`[generate_worker] could not read source '${name}' (${url}): ${e.message}`);
    return "";
  }
}

// --- Queue claim (oldest queued -> running) ---------------------------------
async function claimNextJob() {
  // Atomically-ish claim: pick the oldest 'queued' row and mark it 'running'.
  // The attempt++ protects against a double-tick racing the same row: we only
  // flip rows whose attempt matches what we read, so a concurrent worker that
  // also claims this row is a no-op. (Two concurrent invocations are rare on the
  // 30s cron, but this keeps the worker safely re-entrant.)
  const pick = new URLSearchParams({
    select: "id,job_data,status,attempt",
    status: "eq.queued",
    order: "created_at.asc",
    limit: "1",
  });
  const resp = await fetch(`${SUPABASE_URL}/rest/v1/generation_jobs?${pick}`, { headers: sbAuth() });
  if (!resp.ok) throw new Error(`claim fetch: HTTP ${resp.status}`);

  const rows = await resp.json();
  const row = rows?.[0];
  if (!row || !row.id) return null; // queue empty — idle tick

  const expectedAttempt = row.attempt ?? 0;
  const novaAttempt = expectedAttempt + 1;
  const claimQ = new URLSearchParams({
    id: `eq.${row.id}`,
    status: "eq.queued",              // only claim if still queued
    attempt: `eq.${expectedAttempt}`, // only claim if nobody else advanced it
  });
  const claimed = await fetch(`${SUPABASE_URL}/rest/v1/generation_jobs?${claimQ}`, {
    method: "PATCH",
    headers: { ...sbAuth(), Prefer: "return=representation" },
    body: JSON.stringify({ status: "running", attempt: novaAttempt }),
  });
  if (!claimed.ok) return null; // mismatched attempt — another worker won
  const claimedRows = await claimed.json();
  const claimedRow = claimedRows?.[0];
  if (!claimedRow) return null; // no longer queued concurrently
  return claimedRow;
}

// --- Persistence (same shape as the old synchronous generator) -----------------
function slugify(s) {
  return (
    (s || "").toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "").slice(0, 80) || "untitled"
  );
}

async function resolveJobId(job) {
  const q = new URLSearchParams({
    select: "id,title,company",
    title: `eq.${job.title}`,
    company: `eq.${job.company}`,
    limit: "1",
  });
  const found = await fetch(`${SUPABASE_URL}/rest/v1/jobs?${q}`, { headers: sbAuth() });
  if (found.ok) {
    const foundRows = await found.json();
    if (foundRows?.[0]?.id) return foundRows[0].id;
  }

  const canonical_url = `generated://${slugify(job.company)}/${slugify(job.title)}`;
  const created = await fetch(`${SUPABASE_URL}/rest/v1/jobs?on_conflict=canonical_url`, {
    method: "POST",
    headers: { ...sbAuth(), Prefer: "resolution=merge-duplicates,return=representation" },
    body: JSON.stringify({
      canonical_url,
      source: "generated",
      application_route: "On-demand (dashboard): generate",
      application_route_type: "On-demand (dashboard): generate",
      listing_verification: "Generated from verified candidate profile",
      title: job.title,
      company: job.company,
      location: job.location || "Melbourne",
      description: (job.description || "").slice(0, 1200),
    }),
  });
  if (!created.ok) throw new Error(`upsert job: HTTP ${created.status}`);
  const createdRows = await created.json();
  return createdRows?.[0]?.id;
}

async function upsertDocument(jobId, type, content, model) {
  const resp = await fetch(
    `${SUPABASE_URL}/rest/v1/application_documents?on_conflict=job_id,user_id,document_type,format`,
    {
      method: "POST",
      headers: { ...sbAuth(), Prefer: "resolution=merge-duplicates,return=representation" },
      body: JSON.stringify({
        job_id: jobId,
        user_id: LOCAL_USER_ID,
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
    throw (e); // worker must mark the queue row 'error' on persistence failure
  }
}

// Mark a generation_jobs row completed or failed.
async function finishJob(jobId, status, { applicationId = null, error = null } = {}) {
  const body = { status, completed_at: new Date().toISOString() };
  if (applicationId) body.application_id = applicationId;
  if (error) body.error = String(error).slice(0, 400);
  const resp = await fetch(`${SUPABASE_URL}/rest/v1/generation_jobs?id=eq.${jobId}`, {
    method: "PATCH",
    headers: sbAuth(),
    body: JSON.stringify(body),
  });
  return resp.ok;
}

// --- Handler ------------------------------------------------------------
Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: corsHeaders });

  if (!SUPABASE_URL || !SERVICE_KEY) {
    return corsResponse(503, { error: "SUPABASE_URL / SERVICE_ROLE_KEY not configured" });
  }

  // Claim the oldest queued job. If the queue is empty, this is an idle tick —
  // return success with processed:0 (callers treat it as a no-op heartbeat).
  let job;
  try {
    job = await claimNextJob();
  } catch (e) {
    console.error(`[generate_worker] claim failed: ${e.message}`);
    return corsResponse(200, { processed: 0, error: `claim failed: ${e.message}` });
  }
  if (!job) return corsResponse(200, { processed: 0 });

  const payload = job.job_data || {};
  const title = payload.title || "";
  const company = payload.company || "";
  const description = (payload.description || "").slice(0, 1200);
  const why = payload.why || "";
  const location = payload.location || "";

  try {
    // Source of truth: prefer the curated Master Resume (canonical record for
    // AI generation), falling back to the legacy resume.md if unreachable.
    // Both are pulled from public raw.githubusercontent.com (see fetchSource).
    const resume = await fetchSource("master-resume.md") || await fetchSource("resume.md");
    const profile = await fetchSource("job_profile.json");
    const guidelines = await fetchSource("agent_prompt.md");

    // ── Generation instructions: Voice Guide + Tailoring + Cover Letter ──────
    // Derived from Guidelines/Resume & Cover Letter Generation — Combined Agent
    // Prompt + Shared Voice Guide (Sam's voice rules). Fed verbatim to the LLM
    // so tone, tailoring, source-of-truth and anti-fabrication rules always apply.
    const systemPrompt = `You are Sam Ludwig's recruitment agent. You generate a tailored
résumé and cover letter for a specific job listing, using ONLY Sam's real, verified
career record as the source of truth. You never invent skills, employers, metrics,
titles, dates, or quals.

ABSOLUTE RULES:
- SOURCE OF TRUTH: Every resume/cover letter is a subset, reordering, or rewording of
  content that already exists in the candidate's real record. Never introduce a skill,
  tool, achievement, metric, employer, or title not already present.
- VOICE: confident, plain-spoken, slightly understated. Lead with the action/outcome,
  not the task. Avoid passive voice. No exclamations, no rhetorical questions, no
  emoji, no bold/italic emphasis inside the documents. Australian English spelling
  (organise, licence, standardise, prioritise). Technical terms capitalised exactly as
  vendors do (Microsoft Intune, Entra ID, ServiceNow, SharePoint Online).
- Resume bullets start with a past-tense verb, no trailing period unless multisentence,
  structurally parallel within a section.
- RELEVANCE CHECK FIRST: classify the role Strong / Adjacent / No match. If no
  meaningful overlap, do NOT generate — instead output a "⚠️ Resume not generated"
  flag message (match assessment, why, closest overlap, options) and stop.
- TAILOR substance, not just labels: reorder/reword to the role, foreground the most
  relevant real achievements, only use quantified metrics that exist in the record.
- Format section order consistently: Header → Target Role → Professional Summary →
  Skills → Professional Experience → Selected Projects → Certifications & Education.
- COVER LETTER: 250-400 words. Opening names role+company and a real reason; fit
  paragraph connects 2-3 real outcomes to the listing's stated requirements; value
  paragraph is specific, not boilerplate; confident brief close. Never restate the
  resume line-by-line; never fabricate enthusiasm.
- Never leave scratchpad/listing-meta text in the final document.
- Finish with the tailring/self-check summary block.

${guidelines ? `ADDITIONAL GUIDELINES (verbatim, follow these exactly):
${guidelines}` : ""}`;

    const userPrompt = `Candidate real record (VERIFIED FACT — source of truth):
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
    if (result.error) throw new Error(result.error);

    const SEP = "===COVER_LETTER===";
    const idx = result.content.indexOf(SEP);
    let resumeMd = result.content;
    let coverMd = "";
    if (idx >= 0) {
      resumeMd = result.content.slice(0, idx).trim();
      coverMd = result.content.slice(idx + SEP.length).trim();
    }

    const applicationId = await persistApplication(
      { title, company, location, description: payload.description || "" },
      resumeMd,
      coverMd,
      result.model || Deno.env.get("LLM_MODEL") || "deepseek/deepseek-v4-flash-0731",
    );

    await finishJob(job.id, "completed", { applicationId });
    console.log(`[generate_worker] job ${job.id} completed (application ${applicationId})`);
    return corsResponse(200, { processed: 1, job_id: job.id, application_id: applicationId, status: "completed" });
  } catch (e) {
    await finishJob(job.id, "error", { error: e.message });
    console.error(`[generate_worker] job ${job.id} failed: ${e.message}`);
    return corsResponse(200, { processed: 1, job_id: job.id, status: "error", error: String(e.message).slice(0, 400) });
  }
});