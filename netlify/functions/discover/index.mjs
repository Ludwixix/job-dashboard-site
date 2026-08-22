// netlify/functions/discover/index.mjs
// Job discovery: fetches from Adzuna + LinkedIn (via web search) and stores in Supabase

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

const canonicalise = (url) => {
  try {
    const u = new URL(url);
    u.hash = '';
    for (const k of [...u.searchParams.keys()]) {
      if (/^(utm_|fbclid$|gclid$|mc_|ref$|source$)/i.test(k)) u.searchParams.delete(k);
    }
    u.searchParams.sort();
    return `${u.origin}${u.pathname.replace(/\/$/, '')}${u.search}`;
  } catch { return null; }
};

const fetchAdzuna = async (page = 1) => {
  const appId = process.env.ADZUNA_APP_ID;
  const appKey = process.env.ADZUNA_APP_KEY;
  if (!appId || !appKey) throw new Error('Adzuna credentials not configured');

  const queries = [
    'Azure Microsoft 365 Intune endpoint infrastructure technician',
    'IT support service desk analyst Melbourne',
    'cloud engineer DevOps infrastructure',
    'network technician cabling field',
    'horticulture groundskeeper parks',
    'warehouse logistics forklift'
  ];

  const allJobs = [];
  for (const q of queries) {
    try {
      const resp = await fetch(
        `https://api.adzuna.com/v1/api/jobs/au/search/${page}?app_id=${appId}&app_key=${appKey}&results_per_page=50&what=${encodeURIComponent(q)}&where=Melbourne&content-type=application/json`,
        { signal: AbortSignal.timeout(15000) }
      );
      if (!resp.ok) continue;
      const data = await resp.json();
      if (data.results) allJobs.push(...data.results);
    } catch (e) {
      console.error(`Adzuna query failed: ${q}`, e.message);
    }
  }
  return allJobs;
};

const normaliseAdzuna = (raw) => {
  const route = raw.redirect_url || raw.job_url || raw.url || '';
  const canonicalUrl = canonicalise(route);
  const title = String(raw.title || '').trim();
  const company = String(raw.company?.display_name || raw.company || '').trim();
  if (!title || !company || !canonicalUrl) return null;

  return {
    source: 'adzuna',
    source_record_id: raw.id ? String(raw.id) : canonicalUrl,
    canonical_url: canonicalUrl,
    application_route: route,
    application_route_type: 'Adzuna listing',
    listing_verification: 'Aggregator listing; confirm the original employer route and requirements before applying.',
    title,
    company,
    location: raw.location?.display_name || 'Melbourne',
    description: String(raw.description || '').replace(/<[^>]+>/g, '').slice(0, 10000),
    work_type: raw.contract_type || raw.category?.label || '',
    remote: /remote|work from home|hybrid/i.test(`${raw.title || ''} ${raw.description || ''}`),
    posted_at: raw.created || null,
    is_expired: false,
    fit: 'Review',
    matched_terms: [],
    gaps: [],
    requirements_to_confirm: ['Confirm listing is still open'],
    needs_human_review: true
  };
};

// LinkedIn search via web scraping (Adzuna sometimes indexes LinkedIn cross-posts)
const fetchLinkedInViaAdzuna = async () => {
  // Search for LinkedIn-sourced jobs on Adzuna (they appear as aggregations)
  const appId = process.env.ADZUNA_APP_ID;
  const appKey = process.env.ADZUNA_APP_KEY;
  if (!appId || !appKey) return [];

  try {
    const resp = await fetch(
      `https://api.adzuna.com/v1/api/jobs/au/search/1?app_id=${appId}&app_key=${appKey}&results_per_page=50&what=IT+infrastructure+Melbourne&where=Melbourne&content-type=application/json&max_days_old=14`,
      { signal: AbortSignal.timeout(15000) }
    );
    if (!resp.ok) return [];
    const data = await resp.json();
    return (data.results || []).filter(j => {
      const url = j.redirect_url || j.url || '';
      // Include jobs from employer sites (direct applications) even if originally from LinkedIn
      return !url.includes('linkedin.com');
    });
  } catch { return []; }
};

const INDEED_QUERIES = [
  'IT support Melbourne',
  'Azure engineer Melbourne',
  'Microsoft 365 Melbourne',
  'infrastructure technician Melbourne',
  'service desk analyst Melbourne'
];

const fetchIndeed = async () => {
  // Indeed via JobSpy or direct scraping isn't available server-side without credentials
  // Return empty for now — can be added later
  return [];
};

export default async (request) => {
  // Verify cron secret or manual trigger
  const authHeader = request.headers.get('authorization') || '';
  const cronSecret = process.env.CRON_SECRET || process.env.JOB_INGEST_API_TOKEN || '';
  const isCron = request.headers.get('x-netlify-cron') === 'true';
  const hasToken = authHeader.includes(cronSecret) && cronSecret.length > 0;

  if (!isCron && !hasToken && request.method === 'GET') {
    return json(200, {
      status: 'ready',
      message: 'Job discovery endpoint. POST with authorization to trigger. Runs daily via Netlify cron.',
      sources: ['adzuna', 'indeed (planned)'],
      queries: INDEED_QUERIES.length + 6
    });
  }

  console.log('=== Job Discovery Starting ===');
  const startTime = Date.now();

  try {
    // Fetch from Adzuna
    const adzunaJobs = await fetchAdzuna();
    const linkedinJobs = await fetchLinkedInViaAdzuna();
    const allRaw = [...adzunaJobs, ...linkedinJobs];

    console.log(`Fetched ${allRaw.length} raw jobs from Adzuna`);

    // Normalise and deduplicate
    const seen = new Set();
    const jobs = [];
    for (const raw of allRaw) {
      const normalised = normaliseAdzuna(raw);
      if (!normalised) continue;
      if (seen.has(normalised.canonical_url)) continue;
      seen.add(normalised.canonical_url);
      jobs.push(normalised);
    }

    console.log(`Normalised to ${jobs.length} unique jobs`);

    if (jobs.length === 0) {
      return json(200, { status: 'ok', jobs_found: 0, message: 'No new jobs found' });
    }

    // Store in Supabase via ingest endpoint or direct insert
    const supabaseUrl = process.env.SUPABASE_URL?.replace(/\/$/, '');
    const key = process.env.SUPABASE_SECRET_KEY;

    // Batch upsert — 50 at a time
    let stored = 0;
    for (let i = 0; i < jobs.length; i += 50) {
      const batch = jobs.slice(i, i + 50);
      try {
        const resp = await fetch(`${supabaseUrl}/rest/v1/jobs?on_conflict=canonical_url`, {
          method: 'POST',
          headers: {
            apikey: key,
            Authorization: `Bearer ${key}`,
            'Content-Type': 'application/json',
            Prefer: 'resolution=merge-duplicates,return=minimal'
          },
          body: JSON.stringify(batch)
        });
        const respText = await resp.text();
        if (resp.ok) stored += batch.length;
        else {
          console.error(`Batch upsert failed (${resp.status}):`, respText.slice(0, 500));
        }
      } catch (e) {
        console.error(`Batch error: ${e.message}`);
      }
    }

    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    console.log(`Discovery complete: ${stored} jobs stored in ${elapsed}s`);

    return json(200, {
      status: 'ok',
      jobs_found: jobs.length,
      jobs_stored: stored,
      elapsed_seconds: parseFloat(elapsed),
      sources: {
        adzuna: adzunaJobs.length,
        linkedin: linkedinJobs.length
      }
    });
  } catch (e) {
    console.error('Discovery failed:', e);
    return json(500, { error: 'discovery failed', detail: String(e.message).slice(0, 500) });
  }
};
