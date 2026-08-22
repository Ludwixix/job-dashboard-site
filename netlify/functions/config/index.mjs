// netlify/functions/config/index.mjs
// Return public config for dashboard — includes Supabase URL/key for client auth

export default async () => {
  const config = {
    supabaseUrl: process.env.SUPABASE_URL || '',
    supabasePublishableKey: process.env.SUPABASE_PUBLISHABLE_KEY || '',
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
