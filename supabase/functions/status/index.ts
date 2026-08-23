// Supabase Edge Function: poll generation job status.
//
//   GET /status?job_id=<uuid>
//     -> 200 { job_id, status, error, application_id, completed_at }
//            status: queued | running | completed | error
//     -> 404 { error }   job_id not found / missing
//
// The frontend calls this every few seconds after POST /generate returns a
// job_id; when status becomes 'completed' it refreshes the saved-applications
// list and renders the per-card download row. Runs with SERVICE ROLE for the
// read (bypasses RLS) so no privileged key ever reaches the browser.

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
  if (req.method !== "GET") return corsResponse(405, { error: "method not allowed" });
  if (!SUPABASE_URL || !SERVICE_KEY) {
    return corsResponse(503, { error: "SUPABASE_URL / SERVICE_ROLE_KEY not configured" });
  }

  const jobId = new URL(req.url).searchParams.get("job_id");
  if (!jobId) return corsResponse(400, { error: "missing ?job_id=" });

  const q = new URLSearchParams({
    select: "id,status,error,application_id,completed_at,created_at,updated_at",
    id: `eq.${jobId}`,
    limit: "1",
  });
  const resp = await fetch(`${SUPABASE_URL}/rest/v1/generation_jobs?${q}`, { headers: sbAuth() });
  if (!resp.ok) return corsResponse(502, { error: `supabase ${resp.status}` });

  const rows = await resp.json();
  const row = rows?.[0];
  if (!row) return corsResponse(404, { error: "job not found" });

  return corsResponse(200, {
    job_id: row.id,
    status: row.status,
    error: row.error ?? null,
    application_id: row.application_id ?? null,
    completed_at: row.completed_at ?? null,
  });
});