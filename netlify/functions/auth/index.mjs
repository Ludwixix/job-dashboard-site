// netlify/functions/auth/index.mjs
// Supabase auth proxy — signup, signin, signout, session refresh

const json = (status, body) => new Response(JSON.stringify(body), {
  status,
  headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' }
});

export default async (request) => {
  const supabaseUrl = process.env.SUPABASE_URL?.replace(/\/$/, '');
  const anonKey = process.env.SUPABASE_PUBLISHABLE_KEY;
  if (!supabaseUrl || !anonKey) return json(500, { error: 'supabase not configured' });

  const url = new URL(request.url);
  const action = url.searchParams.get('action') || 'signin';

  let body;
  try { body = await request.json(); } catch { body = {}; }

  const headers = {
    apikey: anonKey,
    'Content-Type': 'application/json',
    'X-Supabase-Auth-Api-Version': '2021-11-09'
  };

  let endpoint;
  let payload;

  switch (action) {
    case 'signup':
      endpoint = '/auth/v1/signup';
      payload = { email: body.email, password: body.password, data: body.data || {} };
      break;
    case 'signin':
      endpoint = '/auth/v1/token?grant_type=password';
      payload = { email: body.email, password: body.password };
      break;
    case 'signout':
      const signoutToken = request.headers.get('authorization')?.replace(/^Bearer\s+/i, '');
      if (signoutToken) {
        await fetch(`${supabaseUrl}/auth/v1/logout`, {
          method: 'POST',
          headers: { ...headers, Authorization: `Bearer ${signoutToken}` }
        });
      }
      return json(200, { success: true });
    case 'refresh':
      endpoint = '/auth/v1/token?grant_type=refresh_token';
      payload = { refresh_token: body.refresh_token };
      break;
    case 'session':
      // Validate existing session
      const sessionToken = request.headers.get('authorization')?.replace(/^Bearer\s+/i, '');
      if (!sessionToken) return json(401, { error: 'no token' });
      const userResp = await fetch(`${supabaseUrl}/auth/v1/user`, {
        headers: { Authorization: `Bearer ${sessionToken}`, apikey: anonKey }
      });
      if (!userResp.ok) return json(401, { error: 'invalid session' });
      const user = await userResp.json();
      return json(200, { user: { id: user.id, email: user.email } });
    default:
      return json(400, { error: `unknown action: ${action}` });
  }

  try {
    const resp = await fetch(`${supabaseUrl}${endpoint}`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload)
    });
    const result = await resp.json();
    if (!resp.ok) return json(resp.status, result);
    return json(200, result);
  } catch (e) {
    return json(500, { error: 'auth failed', detail: String(e.message).slice(0, 200) });
  }
};
