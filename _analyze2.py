import json
from pathlib import Path
ROOT = Path(r'C:\Users\samlu\.openclaw\workspace')
for cand in [ROOT/'jobs_nonlinkedin_2026-08-08.json', ROOT/'job-dashboard-site'/'jobs_nonlinkedin_2026-08-08.json']:
    if cand.exists():
        DATA = cand; break
data = json.loads(DATA.read_text(encoding='utf-8'))
for k in ['filtered_at','filtered_cutoff','filtered_end','freshness_policy','policy','updated','count','search_area']:
    print(f'== {k} ==')
    print(json.dumps(data.get(k), indent=2, ensure_ascii=False))
    print()
for j in data['jobs']:
    if str(j.get('posted') or '') >= '2026-08-17':
        print('== FRESH JOB FULL ==')
        print(json.dumps(j, indent=2, ensure_ascii=False))
