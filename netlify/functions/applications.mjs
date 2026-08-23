// netlify/functions/applications.mjs
// Backs the "Saved applications" library on the front end.
//
//   GET      /.netlify/functions/applications
//            -> { saved: [ { id, title, company, location, createdAt,
//                           docs: [ { id, type, content, createdAt } ] } ] }
//   DELETE   /.netlify/functions/applications?id=<documentId>
//            -> delete a single document (resume or cover letter)
//   DELETE   /.netlify/functions/applications?jobId=<jobId>
//            -> delete the job row (cascades its documents via FK), plus any
//               status_history rows (no FK between them, so explicit)
//
// The service role key stays server-side here; the browser never touches the
// Supabase REST endpoint or carries a key. RLS is bypassed by the service role,
// same trust model as generate.mjs and the n8n pipeline.

const SUPABASE_URL = (process.env.SUPABASE_URL || "").replace(/\/+$/, "");
const SUPABASE_KEY =
  process.env.SUPABASE_SERVICE_ROLE_KEY ||
  process.env.SUPABASE_SERVICE_KEY ||
  process.env.SUPABASE_ANON_KEY ||
  "";

function supabaseHeaders() {
  return {
    apikey: SUPABASE_KEY,
    Authorization: `Bearer ${SUPABASE_KEY}`,
    "Content-Type": "application/json",
  };
}

// GET: list generated applications, newest first, each with its documents.
async function listApplications() {
  const q = new URLSearchParams({
    select: "id,content,document_type,created_at,jobs(id,title,company,location)",
    order: "created_at.desc",
    limit: "200",
  });
  const resp = await fetch(`${SUPABASE_URL}/rest/v1/application_documents?${q}`, {
    headers: supabaseHeaders(),
  });
  if (!resp.ok) return { error: `supabase ${resp.status}` };

  const rows = await resp.json();
  const byJob = new Map();
  for (const row of rows) {
    const j = row.jobs;
    if (!j) continue;
    const key = j.id;
    if (!byJob.has(key)) {
      byJob.set(key, {
        id: key,
        title: j.title,
        company: j.company,
        location: j.location,
        createdAt: j.created_at,
        docs: [],
      });
    }
    byJob.get(key).docs.push({
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
    headers: supabaseHeaders(),
  });
  return resp.ok ? null : `supabase ${resp.status}`;
}

async function deleteApplication(jobId) {
  // application_documents cascade via FK; status_history does not, so remove it explicitly.
  await fetch(`${SUPABASE_URL}/rest/v1/status_history?job_id=eq.${jobId}`, {
    method: "DELETE",
    headers: supabaseHeaders(),
  });
  const resp = await fetch(`${SUPABASE_URL}/rest/v1/jobs?id=eq.${jobId}`, {
    method: "DELETE",
    headers: supabaseHeaders(),
  });
  return resp.ok ? null : `supabase ${resp.status}`;
}

export const handler = async (event) => {
  if (!SUPABASE_URL || !SUPABASE_KEY) {
    return {
      statusCode: 503,
      body: JSON.stringify({
        error: "SUPABASE_URL / SUPABASE_SERVICE_KEY not configured",
      }),
    };
  }

  const method = event.httpMethod || "GET";

  if (method === "GET") {
    const result = await listApplications();
    if (result.error) {
      return { statusCode: 502, body: JSON.stringify({ error: result.error }) };
    }
    return {
      statusCode: 200,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(result),
    };
  }

  if (method === "DELETE") {
    const params = new URLSearchParams(event.rawQuery || "");
    const docId = params.get("id");
    const jobId = params.get("jobId");

    if (docId) {
      const err = await deleteDocument(docId);
      if (err) return { statusCode: 502, body: JSON.stringify({ error: err }) };
      return { statusCode: 200, body: JSON.stringify({ ok: true, deleted: "document" }) };
    }
    if (jobId) {
      const err = await deleteApplication(jobId);
      if (err) return { statusCode: 502, body: JSON.stringify({ error: err }) };
      return { statusCode: 200, body: JSON.stringify({ ok: true, deleted: "application" }) };
    }
    return { statusCode: 400, body: JSON.stringify({ error: "missing ?id= or ?jobId=" }) };
  }

  return { statusCode: 405, body: JSON.stringify({ error: "method not allowed" }) };
};