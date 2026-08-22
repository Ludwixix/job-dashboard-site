// netlify/functions/apply/index.mjs
// Handle auto-apply: mark job as Applied, log the action
// Does NOT actually submit applications — just tracks status

const json = (status, body) => new Response(JSON.stringify(body), {
  status,
  headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' }
});

export default async (request) => {
  if (request.method !== 'POST') return json(405, { error: 'method not allowed' });

  const supabaseUrl = process.env.SUPABASE_URL?.replace(/\/$/, '');
  const key = process.env.SUPABASE_SECRET_KEY;
  const anonKey = process.env.SUPABASE_PUBLISHABLE_KEY;
  if (!supabaseUrl || !key) return json(500, { error: 'supabase not configured' });

  // Auth check
  const authHeader = request.headers.get('authorization') || '';
  const token = authHeader.replace(/^Bearer\s+/i, '').trim();
  if (!token || token.length < 10) return json(401, { error: 'auth required' });

  let user;
  try {
    const userResp = await fetch(`${supabaseUrl}/auth/v1/user`, {
      headers: { Authorization: `Bearer ${token}`, apikey: anonKey || key }
    });
    if (!userResp.ok) return json(401, { error: 'invalid session' });
    user = await userResp.json();
  } catch {
    return json(401, { error: 'auth check failed' });
  }

  // Check owner
  const ownerUserId = process.env.DASHBOARD_OWNER_USER_ID;
  if (ownerUserId && user.id !== ownerUserId) return json(403, { error: 'not owner' });

  let body;
  try { body = await request.json(); } catch { return json(400, { error: 'invalid JSON' }); }

  const { job_id, action } = body;
  if (!job_id) return json(400, { error: 'job_id required' });

  // Update job status
  const updateData = {
    fit: action === 'applied' ? 'Applied' : action === 'rejected' ? 'Rejected' : 'Review',
    needs_human_review: false
  };

  try {
    const resp = await fetch(`${supabaseUrl}/rest/v1/jobs?id=eq.${encodeURIComponent(job_id)}`, {
      method: 'PATCH',
      headers: {
        apikey: key,
        Authorization: `Bearer ${key}`,
        'Content-Type': 'application/json',
        Prefer: 'return=representation'
      },
      body: JSON.stringify(updateData)
    });

    if (!resp.ok) {
      const err = await resp.text();
      return json(502, { error: 'update failed', detail: err.slice(0, 300) });
    }

    const updated = await resp.json();
    return json(200, {
      success: true,
      job_id,
      new_status: updateData.fit,
      timestamp: new Date().toISOString(),
      message: action === 'applied'
        ? 'Marked as Applied. Remember to actually submit your application!'
        : `Status changed to ${updateData.fit}`
    });
  } catch (e) {
    return json(500, { error: 'apply failed', detail: String(e.message).slice(0, 300) });
  }
};
