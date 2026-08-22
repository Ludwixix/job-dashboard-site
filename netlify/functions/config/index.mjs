// netlify/functions/config/index.mjs
// Return public config (no secrets) — used by dashboard to check features

export default async () => {
  const config = {
    features: {
      ai_generate: !!process.env.OPENROUTER_API_KEY,
      job_discovery: !!process.env.ADZUNA_APP_ID,
      auth: !!process.env.SUPABASE_URL,
      auto_apply: true
    },
    sources: ['adzuna', 'indeed'],
    version: '2.0.0',
    updated: new Date().toISOString()
  };

  return new Response(JSON.stringify(config), {
    status: 200,
    headers: { 'content-type': 'application/json', 'cache-control': 'public, max-age=300' }
  });
};
