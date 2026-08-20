import json, collections, datetime
from pathlib import Path
ROOT = Path(r'C:\Users\samlu\.openclaw\workspace')
# The authoritative data file lives at workspace root AND is copied into the site.
for cand in [ROOT/'jobs_nonlinkedin_2026-08-08.json', ROOT/'job-dashboard-site'/'jobs_nonlinkedin_2026-08-08.json']:
    if cand.exists():
        print('DATA FILE:', cand)
        DATA = cand
        break
data = json.loads(DATA.read_text(encoding='utf-8'))
print('TOP KEYS:', sorted(data.keys()))
print('updated:', data.get('updated'))
print('count:', data.get('count'))
print('search_area:', data.get('search_area'))
jobs = data.get('jobs', [])
sections = data.get('sections', {}) or {}
print('CORE jobs:', len(jobs))
print('SECTIONS:', {k: len(v) for k, v in sections.items()})
allj = jobs + [j for v in sections.values() for j in v]
print('TOTAL roles:', len(allj))
print('SAMPLE JOB KEYS:', sorted(allj[0].keys()) if allj else 'none')

# posted-date distribution
posts = collections.Counter()
for j in allj:
    posts[str(j.get('posted') or 'MISSING')] += 1
print('\nPOSTED DATE DISTRIBUTION:')
for k in sorted(posts.keys()):
    print(f'  {k}: {posts[k]}')

# How many within 96h of 2026-08-21T02:54+10:00 (cutoff date 2026-08-17)
cutoff = '2026-08-17'
fresh = [j for j in allj if str(j.get('posted') or '') >= cutoff]
print(f'\nFRESH (posted >= {cutoff}):', len(fresh))
for j in fresh:
    print(f"   {j.get('posted')} | {j.get('company')} | {j.get('title')} | {j.get('source')}")

# Check which fresh roles have materials present
app = ROOT/'job-dashboard-site'/'applications'
aud = ROOT/'job-dashboard-site'/'application_audits'
print('\nFRESH ROLES MATERIAL STATUS:')
for j in fresh:
    resume = j.get('resume','')
    rp = ROOT/'job-dashboard-site'/resume if resume else None
    exists = rp.exists() if rp else False
    print(f"   {j.get('company')[:22]:22} resume_pdf={'Y' if exists else 'N'} route={j.get('application_route_type','')[:30]}")
