// Supabase Edge Function: saved-applications library (read + delete).
// Replaces the former Netlify function of the same purpose.
//
//   GET    -> { saved: [ { id, title, company, location, createdAt,
//                          docs: [ { id, type, content, createdAt } ] } ] }
//   DELETE ?id=<documentId>   -> delete one resume/cover letter
//   DELETE ?jobId=<jobId>     -> delete the job (cascades docs) + its status history
//
// Runs with SERVICE ROLE (injected server-side) so the frontend never handles a
// privileged key. The endpoint itself is public — acceptable for a personal
// dashboard; gate behind a shared token or Supabase Auth if it ever becomes more.

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

async function listApplications() {
  const q = new URLSearchParams({
    select: "id,content,document_type,created_at,jobs(id,title,company,location)",
    order: "created_at.desc",
    limit: "200",
  });
  const resp = await fetch(`${SUPABASE_URL}/rest/v1/application_documents?${q}`, { headers: sbAuth() });
  if (!resp.ok) return { error: `supabase ${resp.status}` };

  const rows = await resp.json();
  const byJob = new Map();
  for (const row of rows) {
    const j = row.jobs;
    if (!j) continue;
    if (!byJob.has(j.id)) {
      byJob.set(j.id, {
        id: j.id,
        title: j.title,
        company: j.company,
        location: j.location,
        createdAt: j.created_at,
        docs: [],
      });
    }
    byJob.get(j.id).docs.push({
      id: row.id,
      type: row.document_type,
      content: row.content,
      createdAt: row.created_at,
    });
  }
  return { saved: [...byJob.values()] };
}

async function deleteDocument(docId) {
  const resp = await fetch(`${SUPABASE_URL}/rest/v1/application_documents?id=eq.${docId}`, {
    method: "DELETE",
    headers: sbAuth(),
  });
  return resp.ok ? null : `supabase ${resp.status}`;
}

async function deleteApplication(jobId) {
  await fetch(`${SUPABASE_URL}/rest/v1/status_history?job_id=eq.${jobId}`, {
    method: "DELETE",
    headers: sbAuth(),
  });
  const resp = await fetch(`${SUPABASE_URL}/rest/v1/jobs?id=eq.${jobId}`, { method: "DELETE", headers: sbAuth() });
  return resp.ok ? null : `supabase ${resp.status}`;
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: corsHeaders });

  if (!SUPABASE_URL || !SERVICE_KEY) {
    return corsResponse(503, { error: "SUPABASE_URL / SERVICE_ROLE_KEY not configured" });
  }

  const url = new URL(req.url);
  const method = req.method;

  if (method === "GET") {
    const result = await listApplications();
    if (result.error) return corsResponse(502, { error: result.error });
    return corsResponse(200, result);
  }

  if (method === "DELETE") {
    const docId = url.searchParams.get("id");
    const jobId = url.searchParams.get("jobId");
    if (docId) {
      const err = await deleteDocument(docId);
      if (err) return corsResponse(502, { error: err });
      return corsResponse(200, { ok: true, deleted: "document" });
    }
    if (jobId) {
      const err = await deleteApplication(jobId);
      if (err) return corsResponse(502, { error: err });
      return corsResponse(200, { ok: true, deleted: "application" });
    }
    return corsResponse(400, { error: "missing ?id= or ?jobId=" });
  }

  return corsResponse(405, { error: "method not allowed" });
});