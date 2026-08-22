// netlify/functions/ingest/index.mjs
// Accept jobs from n8n, discover, or manual trigger and store in Supabase

const json = (status, body) => new Response(JSON.stringify(body), {
  status,
  headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' }
});

const supabaseRequest = async (path, options = {}) => {
  const base = process.env.SUPABASE_URL?.replace(/\/$/, '');
  const key = process.env.SUPABASE_SECRET_KEY;
  if (!base || !key) throw new Error('Supabase not configured');
  return fetch(`${base}/rest/v1/${path}`, {
    ...options,
    headers: {
      apikey: key,
      Authorization: `Bearer ${key}`,
      'Content-Type': 'application/json',
      ...options.headers
    }
  }).then(async r => {
    const text = await r.text();
    if (!r.ok) throw new Error(`Supabase ${r.status}: ${text.slice(0, 300)}`);
    try { return JSON.parse(text); } catch { return text; }
  });
};

export default async (request) => {
  if (request.method !== 'POST') return json(405, { error: 'method not allowed' });

  // Auth: either cron secret or API token
  const authHeader = request.headers.get('authorization') || '';
  const token = authHeader.replace(/^Bearer\s+/i, '').trim();
  const expectedToken = process.env.JOB_INGEST_API_TOKEN || '';
  const isCron = request.headers.get('x-netlify-cron') === 'true';

  if (!isCron && token !== expectedToken) {
    return json(401, { error: 'unauthorized' });
  }

  let body;
  try { body = await request.json(); } catch { return json(400, { error: 'invalid JSON' }); }

  const jobs = Array.isArray(body?.jobs) ? body.jobs : Array.isArray(body) ? body : [];
  if (!jobs.length) return json(400, { error: 'no jobs provided' });

  // Validate and sanitise
  const validJobs = jobs.filter(j => {
    if (!j.canonical_url || !j.title || !j.company) return false;
    return true;
  }).map(j => ({
    source: j.source || 'unknown',
    source_record_id: j.source_record_id || j.canonical_url,
    canonical_url: j.canonical_url,
    application_route: j.application_route || j.canonical_url,
    application_route_type: j.application_route_type || 'Direct listing',
    listing_verification: j.listing_verification || 'Verify before applying',
    title: String(j.title).trim().slice(0, 300),
    company: String(j.company).trim().slice(0, 200),
    location: String(j.location || 'Melbourne').trim().slice(0, 200),
    description: String(j.description || '').replace(/<[^>]+>/g, '').slice(0, 15000),
    work_type: String(j.work_type || '').slice(0, 100),
    remote: Boolean(j.remote),
    posted_at: j.posted_at || j.created || null,
    is_expired: false,
    // Screening defaults
    screening_score: j.screening_score ?? null,
    fit: j.fit || 'Review',
    matched_terms: j.matched_terms || [],
    evidence: j.evidence || [],
    gaps: j.gaps || [],
    requirements_to_confirm: j.requirements_to_confirm || ['Confirm listing is still open'],
    confidence: j.confidence ?? null,
    needs_human_review: j.needs_human_review ?? true
  }));

  if (!validJobs.length) return json(200, { stored: 0, message: 'all jobs filtered out' });

  // Upsert in batches
  let stored = 0;
  for (let i = 0; i < validJobs.length; i += 50) {
    const batch = validJobs.slice(i, i + 50);
    try {
      const result = await supabaseRequest('jobs?on_conflict=canonical_url', {
        method: 'POST',
        headers: { Prefer: 'resolution=merge-duplicates,return=minimal' },
        body: JSON.stringify(batch)
      });
      stored += batch.length;
    } catch (e) {
      console.error(`Ingest batch ${i} failed:`, e.message);
    }
  }

  return json(200, { stored, total: validJobs.length });
};
