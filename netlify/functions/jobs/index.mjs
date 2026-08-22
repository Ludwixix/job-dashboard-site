// netlify/functions/jobs/index.mjs
// Serve jobs from Supabase to the dashboard

const json = (status, body) => new Response(JSON.stringify(body), {
  status,
  headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' }
});

export default async (request) => {
  const url = new URL(request.url);
  const supabaseUrl = process.env.SUPABASE_URL?.replace(/\/$/, '');
  const key = process.env.SUPABASE_SECRET_KEY;
  const anonKey = process.env.SUPABASE_PUBLISHABLE_KEY;

  if (!supabaseUrl || !key) return json(500, { error: 'supabase not configured' });

  // Auth check — require valid Supabase session
  const authHeader = request.headers.get('authorization') || '';
  const token = authHeader.replace(/^Bearer\s+/i, '').trim();
  if (!token || token.length < 10) return json(401, { error: 'auth required' });

  try {
    const userResp = await fetch(`${supabaseUrl}/auth/v1/user`, {
      headers: { Authorization: `Bearer ${token}`, apikey: anonKey || key }
    });
    if (!userResp.ok) return json(401, { error: 'invalid session' });
  } catch {
    return json(401, { error: 'auth check failed' });
  }

  // Build query
  const limit = Math.min(parseInt(url.searchParams.get('limit') || '200'), 500);
  const offset = parseInt(url.searchParams.get('offset') || '0');
  const expired = url.searchParams.get('expired') || 'false';

  let query = `id,title,company,location,description,work_type,remote,application_route,application_route_type,listing_verification,posted_at,screening_score,fit,matched_terms,gaps,requirements_to_confirm,needs_human_review,source,canonical_url,is_expired,created_at`;
  query += `&is_expired=eq.${expired}`;
  query += `&order=screening_score.desc,created_at.desc`;
  query += `&limit=${limit}&offset=${offset}`;

  const resp = await fetch(`${supabaseUrl}/rest/v1/jobs?${query}`, {
    headers: { apikey: key, Authorization: `Bearer ${key}`, Accept: 'application/json' }
  });

  if (!resp.ok) {
    const err = await resp.text();
    return json(502, { error: 'supabase query failed', detail: err.slice(0, 300) });
  }

  const jobs = await resp.json();

  // Also get document metadata
  const docResp = await fetch(`${supabaseUrl}/rest/v1/application_documents?select=job_id,document_type,format,created_at&limit=1000`, {
    headers: { apikey: key, Authorization: `Bearer ${key}`, Accept: 'application/json' }
  });
  const docs = docResp.ok ? await docResp.json() : [];

  // Attach document info to jobs
  const docMap = {};
  for (const d of docs) {
    if (!docMap[d.job_id]) docMap[d.job_id] = [];
    docMap[d.job_id].push(d.document_type);
  }

  const enriched = jobs.map(j => ({
    ...j,
    has_documents: docMap[j.id] || [],
    document_count: (docMap[j.id] || []).length
  }));

  return json(200, { jobs: enriched, count: enriched.length });
};
