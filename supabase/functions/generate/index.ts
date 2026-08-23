// Supabase Edge Function: submit a generation job to the async queue.
//
// POST { title, company, description, why, location }
//   -> 200 { job_id, status: 'queued' }       (instant — no LLM call, no Storage read)
//   -> 400 { error }                          (missing title/company)
//
// The slow OpenRouter work now happens out-of-band: a worker edge function
// (generate_worker) wakes on an interval via pg_cron+pg_net (or a free GitHub
// Actions cron) and drains rows from the generation_jobs table. The frontend
// polls GET /functions/v1/status?job_id= until status flips to 'completed'.
// This is the SAME file path as the old synchronous generator — but it no
// longer blocks ~2min; it just enqueues.
//
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

const SUPABASE_URL = (Deno.env.get("SUPABASE_URL") || "").replace(/\/+$/, "");
const SERVICE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") || Deno.env.get("SUPABASE_SERVICE_KEY") || "";

function sbAuth() {
  return {
    apikey: SERVICE_KEY,
    Authorization: `Bearer ${SERVICE_KEY}`,
    "Content-Type": "application/json",
  };
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: corsHeaders });

  if (req.method !== "POST") return corsResponse(405, { error: "method not allowed" });
  if (!SUPABASE_URL || !SERVICE_KEY) {
    return corsResponse(503, { error: "SUPABASE_URL / SERVICE_ROLE_KEY not configured" });
  }

  let job;
  try {
    job = await req.json();
  } catch {
    return corsResponse(400, { error: "invalid JSON" });
  }
  if (!job || typeof job !== "object") return corsResponse(400, { error: "invalid JSON" });

  const title = (job.title || "").trim();
  const company = (job.company || "").trim();
  if (!title || !company) return corsResponse(400, { error: "title and company are required" });

  // Keep only the known payload fields so we don't echo arbitrary client data.
  const safePayload = {
    title,
    company,
    description: (job.description || "").slice(0, 1200),
    why: job.why || "",
    location: job.location || "",
  };

  const resp = await fetch(`${SUPABASE_URL}/rest/v1/generation_jobs`, {
    method: "POST",
    headers: { ...sbAuth(), Prefer: "return=representation" },
    body: JSON.stringify({ job_data: safePayload }),
  });
  if (!resp.ok) {
    const body = await resp.text();
    return corsResponse(502, { error: `queue insert: HTTP ${resp.status}: ${body.slice(0, 200)}` });
  }

  const rows = await resp.json();
  const row = rows?.[0];
  if (!row?.id) return corsResponse(502, { error: "queue insert returned no row" });

  return corsResponse(200, { job_id: row.id, status: row.status || "queued" });
});