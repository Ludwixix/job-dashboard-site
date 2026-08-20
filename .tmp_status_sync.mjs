const base = (process.env.SUPABASE_URL || '').replace(/\/$/, '');
const key = process.env.SUPABASE_SECRET_KEY;
const owner = process.env.DASHBOARD_OWNER_USER_ID;
if (!base || !key || !owner) throw new Error('Required Netlify environment is unavailable');
const headers = { apikey: key, Authorization: `Bearer ${key}`, 'Content-Type': 'application/json' };
async function get(path) {
  const response = await fetch(`${base}/rest/v1/${path}`, { headers });
  const text = await response.text();
  if (!response.ok) throw new Error(`GET ${path}: HTTP ${response.status} ${text.slice(0, 400)}`);
  return JSON.parse(text);
}
const jobs = await get('jobs?select=id,application_route,title,company&is_expired=eq.false&limit=500');
const statuses = await get(`job_status?user_id=eq.${encodeURIComponent(owner)}&select=job_id,status,notes,updated_at&order=updated_at.desc`);
const byJob = new Map(statuses.map(item => [item.job_id, item]));
const wanted = [/First Focus/i, /GPK Group/i, /FUJIFILM MicroChannel/i, /LAB3/i, /Rapid Circle/i, /Amazon.com/i, /Amazon Web Services/i, /ICT Support Technician/i, /St Vincent/i, /Canon/i, /LGT Wealth/i, /APM/i];
for (const job of jobs.filter(job => wanted.some(re => re.test(`${job.company} ${job.title}`)))) {
  const status = byJob.get(job.id);
  console.log(JSON.stringify({ id: job.id, company: job.company, title: job.title, status: status?.status || 'New', updated_at: status?.updated_at || null, route: job.application_route }));
}
