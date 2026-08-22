// netlify/functions/gate/index.mjs
// Auth gate — verify Supabase session and return user info

const json = (status, body) => new Response(JSON.stringify(body), {
  status,
  headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' }
});

export default async (request) => {
  const supabaseUrl = process.env.SUPABASE_URL?.replace(/\/$/, '');
  const anonKey = process.env.SUPABASE_PUBLISHABLE_KEY;
  if (!supabaseUrl || !anonKey) return json(500, { error: 'supabase not configured' });

  const authHeader = request.headers.get('authorization') || '';
  const token = authHeader.replace(/^Bearer\s+/i, '').trim();
  if (!token || token.length < 10) return json(401, { error: 'not authenticated', authenticated: false });

  try {
    const resp = await fetch(`${supabaseUrl}/auth/v1/user`, {
      headers: { Authorization: `Bearer ${token}`, apikey: anonKey }
    });
    if (!resp.ok) return json(401, { error: 'invalid session', authenticated: false });
    const user = await resp.json();
    if (!user?.id) return json(401, { error: 'no user', authenticated: false });

    const ownerUserId = process.env.DASHBOARD_OWNER_USER_ID;
    const isOwner = !ownerUserId || user.id === ownerUserId;

    return json(200, {
      authenticated: true,
      is_owner: isOwner,
      user_id: user.id,
      email: user.email || null
    });
  } catch (e) {
    return json(500, { error: 'auth check failed', detail: String(e.message).slice(0, 200) });
  }
};
