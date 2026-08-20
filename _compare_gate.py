import hashlib
from pathlib import Path

a = Path(r'C:\Users\samlu\.openclaw\workspace\supabase\netlify')
b = Path(r'C:\Users\samlu\.openclaw\workspace\job-dashboard-site\netlify')
files = ['edge-functions/site-gate.mjs', 'functions/ai-request.mjs', 'functions/auth.mjs',
         'functions/config.mjs', 'functions/gate.mjs', 'functions/ingest.mjs',
         'functions/jobs.mjs', 'functions/status.mjs']
for f in files:
    h1 = hashlib.sha256((a / f).read_bytes()).hexdigest()
    h2 = hashlib.sha256((b / f).read_bytes()).hexdigest()
    print(f, '=>', 'MATCH' if h1 == h2 else 'DIFFER')

print('--- supabase _redirects ---')
print((a / '_redirects').read_text(encoding='utf-8'))
print('--- site _redirects ---')
print((Path(r'C:\Users\samlu\.openclaw\workspace\job-dashboard-site') / '_redirects').read_text(encoding='utf-8'))
print('--- gate exemption check (supabase source) ---')
for line in (a / 'edge-functions' / 'site-gate.mjs').read_text(encoding='utf-8').splitlines():
    if 'application' in line.lower() or 'excluded' in line.lower():
        print(line.strip())
