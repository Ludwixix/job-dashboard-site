// netlify/functions/documents/index.mjs
// Serve generated application documents (resume, cover letter, email) from Supabase
// Supports: list documents for a job, get specific document content, render as HTML

const json = (status, body) => new Response(JSON.stringify(body), {
  status,
  headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' }
});

const html = (status, body) => new Response(body, {
  status,
  headers: { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store' }
});

// Simple markdown to HTML (no dependencies)
const mdToHtml = (md) => {
  if (!md) return '';
  return md
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/\n- /g, '\n<li>')
    .replace(/(<li>.*$)/gm, '<ul>$1</ul>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>')
    .replace(/^/, '<p>')
    .replace(/$/, '</p>')
    .replace(/<p><(h[1-3]|ul|li)/g, '<$1')
    .replace(/<\/(h[1-3]|ul)><\/p>/g, '</$1>')
    .replace(/<\/li><\/p><ul>/g, '</li>')
    .replace(/<p><li>/g, '<ul><li>')
    .replace(/<\/ul><\/p>/g, '</ul>');
};

export default async (request) => {
  const url = new URL(request.url);
  const supabaseUrl = process.env.SUPABASE_URL?.replace(/\/$/, '');
  const key = process.env.SUPABASE_SECRET_KEY;
  const anonKey = process.env.SUPABASE_PUBLISHABLE_KEY;

  if (!supabaseUrl || !key) return json(500, { error: 'supabase not configured' });

  // Auth check
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

  const jobId = url.searchParams.get('job_id');
  const docType = url.searchParams.get('type'); // resume, cover_letter, opening_email
  const format = url.searchParams.get('format') || 'json'; // json, html, raw

  if (!jobId) return json(400, { error: 'job_id required' });

  let query = `job_id,document_type,format,content,source_model,created_at`;
  query += `&job_id=eq.${encodeURIComponent(jobId)}`;
  if (docType) query += `&document_type=eq.${docType}`;

  const resp = await fetch(`${supabaseUrl}/rest/v1/application_documents?${query}`, {
    headers: { apikey: key, Authorization: `Bearer ${key}`, Accept: 'application/json' }
  });

  if (!resp.ok) {
    const err = await resp.text();
    return json(502, { error: 'query failed', detail: err.slice(0, 300) });
  }

  const docs = await resp.json();

  if (format === 'html' && docs.length === 1) {
    // Render as printable HTML
    const doc = docs[0];
    const title = doc.document_type === 'resume' ? 'Resume' :
                  doc.document_type === 'cover_letter' ? 'Cover Letter' : 'Opening Email';
    return html(200, `<!DOCTYPE html>
<html><head><title>${title}</title>
<style>
  body { font-family: 'Segoe UI', system-ui, sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; color: #1a1a1a; line-height: 1.6; }
  h1 { font-size: 24px; border-bottom: 2px solid #333; padding-bottom: 8px; }
  h2 { font-size: 18px; color: #333; margin-top: 24px; }
  h3 { font-size: 15px; color: #555; }
  strong { color: #000; }
  ul { padding-left: 20px; }
  li { margin: 4px 0; }
  @media print { body { margin: 0; } }
</style></head><body>
<div style="text-align:right; color:#999; font-size:12px;">
  <a href="javascript:window.print()" style="background:#333;color:#fff;padding:6px 12px;border-radius:4px;text-decoration:none;">Print / Save PDF</a>
</div>
${mdToHtml(doc.content)}
<p style="color:#999; font-size:11px; margin-top:40px; border-top:1px solid #ddd; padding-top:8px;">
  Generated ${new Date(doc.created_at).toLocaleDateString('en-AU')} | Model: ${doc.source_model || 'AI'} | Draft for review
</p>
</body></html>`);
  }

  if (format === 'raw' && docs.length === 1) {
    return new Response(docs[0].content, {
      status: 200,
      headers: { 'content-type': 'text/markdown; charset=utf-8' }
    });
  }

  // Default: JSON list (without full content for list mode)
  const lightweight = docs.map(d => ({
    job_id: d.job_id,
    document_type: d.document_type,
    format: d.format,
    created_at: d.created_at,
    preview: (d.content || '').slice(0, 200) + '...'
  }));

  // If content is small, include it
  if (docs.length <= 3) {
    for (let i = 0; i < docs.length; i++) {
      lightweight[i].content = docs[i].content;
    }
  }

  return json(200, { documents: lightweight, count: lightweight.length });
};
