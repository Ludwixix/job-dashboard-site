// netlify/functions/status/index.mjs
// System status endpoint

export default async () => {
  const status = {
    ok: true,
    timestamp: new Date().toISOString(),
    env: {
      supabase: !!process.env.SUPABASE_URL,
      openrouter: !!process.env.OPENROUTER_API_KEY,
      adzuna: !!process.env.ADZUNA_APP_ID,
      owner: !!process.env.DASHBOARD_OWNER_USER_ID
    },
    pipeline: {
      discovery: !!process.env.ADZUNA_APP_ID,
      generation: !!process.env.OPENROUTER_API_KEY,
      storage: !!process.env.SUPABASE_URL
    }
  };

  return new Response(JSON.stringify(status), {
    status: 200,
    headers: { 'content-type': 'application/json', 'cache-control': 'no-store' }
  });
};
