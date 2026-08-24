// Supabase Edge Function: saved-applications library (read + delete).
// Replaces the former Netlify function of the same purpose.
//
//   GET        -> { saved: [ { id, title, company, location, createdAt,
//                             docs: [ { id, type, content, createdAt } ] } ] }
//   GET ?file= <documentId>   -> download ONE document as a file (stable URL):
//                               text/markdown + Content-Disposition attachment
//   DELETE ?id=<documentId>   -> delete one resume/cover letter
//   DELETE ?jobId=<jobId>     -> delete the job (cascades docs) + its status history
//
// The ?file= variant powers persistent "Download" links on each job card: the
// frontend stores the per-document URL and links to it directly, so a saved
// resume/cover letter is reachable at a stable address without a client-side
// print-to-PDF step to merely open the file.
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

async function getDocumentFile(docId) {
  const q = new URLSearchParams({
    select: "id,document_type,content,created_at,jobs(title,company)",
  });
  const resp = await fetch(`${SUPABASE_URL}/rest/v1/application_documents?id=eq.${encodeURIComponent(docId)}&${q}`, { headers: sbAuth() });
  if (!resp.ok) return { error: `supabase ${resp.status}` };
  const rows = await resp.json();
  const row = rows && rows[0];
  if (!row) return { notFound: true };

  const company = row.jobs?.company || "application";
  const title = row.jobs?.title || "document";
  const type = row.document_type === "cover_letter" ? "cover_letter" : "resume";
  const slug = (s) => String(s||"").replace(/[^a-zA-Z0-9]+/g,"_").replace(/^_+|_+$/g,"");
  const ext = type;
  const filename = `${slug(company)}_${slug(title)}_${ext}.md`;

  return { filename, content: row.content || "", contentType: type };
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
    // ?file=<documentId> -> single document as a downloadable file (stable URL).
    const fileId = url.searchParams.get("file");
    if (fileId) {
      // Reject non-UUID ids early so a bad ?file= returns 404, not a Supabase 400.
      if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(fileId)) {
        return corsResponse(404, { error: "document not found" });
      }
      const file = await getDocumentFile(fileId);
      if (file.notFound) return corsResponse(404, { error: "document not found" });
      if (file.error) return corsResponse(502, { error: file.error });
      return new Response(file.content, {
        status: 200,
        headers: {
          ...corsHeaders,
          "Content-Type": "text/markdown; charset=utf-8",
          "Content-Disposition": `attachment; filename="${encodeURIComponent(file.filename)}"`,
        },
      });
    }
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