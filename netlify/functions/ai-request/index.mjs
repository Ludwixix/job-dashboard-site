// netlify/functions/ai-request/index.mjs
// Proxy from dashboard to n8n webhooks for AI generation

const json = (status, body) => new Response(JSON.stringify(body), {
  status,
  headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' }
});

export default async (request) => {
  if (request.method !== 'POST') return json(405, { error: 'method not allowed' });

  // Verify caller has a valid Supabase session
  const authHeader = request.headers.get('authorization') || '';
  const token = authHeader.replace(/^Bearer\s+/i, '').trim();
  if (!token || token.length < 10) return json(401, { error: 'missing auth token' });

  const supabaseUrl = process.env.SUPABASE_URL?.replace(/\/$/, '');
  const anonKey = process.env.SUPABASE_PUBLISHABLE_KEY;
  if (!supabaseUrl || !anonKey) return json(500, { error: 'supabase config missing' });

  try {
    // Validate session
    const userResp = await fetch(`${supabaseUrl}/auth/v1/user`, {
      headers: { Authorization: `Bearer ${token}`, apikey: anonKey }
    });
    if (!userResp.ok) return json(401, { error: 'invalid session' });
    const user = await userResp.json();
    if (!user?.id) return json(401, { error: 'no user id' });

    // Check owner
    const ownerUserId = process.env.DASHBOARD_OWNER_USER_ID;
    if (ownerUserId && user.id !== ownerUserId) return json(403, { error: 'not owner' });

    // Parse request body
    const body = await request.json();
    const { action, job_id } = body;

    if (!action || !job_id) return json(400, { error: 'action and job_id required' });

    // Route to appropriate n8n webhook
    const n8nToken = process.env.N8N_WEBHOOK_TOKEN || '';
    let webhookUrl;

    if (action === 'generate_application') {
      webhookUrl = process.env.N8N_GENERATE_WEBHOOK_URL;
    } else if (action === 'interview_prep') {
      webhookUrl = process.env.N8N_INTERVIEW_PREP_WEBHOOK_URL;
    } else {
      return json(400, { error: `unknown action: ${action}` });
    }

    if (!webhookUrl) return json(500, { error: 'webhook not configured' });

    // Forward to n8n with auth
    const n8nResp = await fetch(webhookUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${n8nToken}`
      },
      body: JSON.stringify({
        action,
        job_id,
        user_id: user.id,
        source: 'dashboard'
      }),
      signal: AbortSignal.timeout(30000)
    });

    const result = await n8nResp.text();
    return new Response(result, {
      status: n8nResp.status,
      headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' }
    });
  } catch (e) {
    return json(502, { error: 'proxy failed', detail: String(e.message).slice(0, 300) });
  }
};
