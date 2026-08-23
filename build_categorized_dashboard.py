#!/usr/bin/env python3
"""Build a self-contained 3-stream job dashboard from JSON data.

Usage:
  python3 build_categorized_dashboard.py [jobs_file.json]
  Defaults to jobs_combined.json in the same directory.

Reads job data, classifies into 3 streams via stream_classifier,
and outputs a self-contained HTML dashboard with dark theme.
"""
import json
import html as html_mod
import hashlib
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Import stream classifier ──────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))
from stream_classifier import classify_all_jobs

# ── Stream metadata ───────────────────────────────────────────────────────
STREAMS = {
    "core-it": {
        "id": "core-it",
        "name": "Core IT & Systems Engineering",
        "icon": "💻",
        "color": "#62d9ff",
        "desc": "Enterprise IT infrastructure, cloud platforms, identity administration, and technical support.",
    },
    "bridge": {
        "id": "bridge",
        "name": "Local \"Bridge\" & Casual Work",
        "icon": "🌉",
        "color": "#ffc857",
        "desc": "Immediate, low-barrier local employment. Casual and part-time roles near St Kilda.",
    },
    "traineeship": {
        "id": "traineeship",
        "name": "Technical Traineeships & Trade Pathways",
        "icon": "🔧",
        "color": "#bda7ff",
        "desc": "Structured on-the-job training, apprenticeships, and employer-sponsored certifications.",
    },
}

# ── Source badge colours ──────────────────────────────────────────────────
SOURCE_COLORS = {
    "linkedin": "#0a66c2",
    "seek": "#3b6fb5",
    "indeed": "#2164f3",
    "adzuna": "#e57200",
}

# ── Helpers ───────────────────────────────────────────────────────────────

def esc(text):
    return html_mod.escape(str(text))


def role_id(job):
    route = job.get("application_route") or job.get("url") or ""
    return hashlib.sha256(route.encode()).hexdigest()[:12]


def relative_date(posted_str):
    """Convert a posted date string to 'N days ago' style."""
    if not posted_str:
        return ""
    try:
        # Try ISO format first
        dt = datetime.fromisoformat(posted_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta = now - dt
        days = delta.days
        if days < 0:
            return "today"
        if days == 0:
            return "today"
        if days == 1:
            return "yesterday"
        if days < 7:
            return f"{days} days ago"
        weeks = days // 7
        if weeks == 1:
            return "1 week ago"
        if weeks < 5:
            return f"{weeks} weeks ago"
        months = days // 30
        if months == 1:
            return "1 month ago"
        return f"{months} months ago"
    except Exception:
        return posted_str


def work_style(job):
    """Determine Onsite / Hybrid / Remote badge."""
    remote = job.get("remote", False)
    location = (job.get("location") or "").lower()
    desc = (job.get("description") or "").lower()
    combined = f"{location} {desc}"

    if remote is True or remote == "true":
        return "Remote"
    if "remote" in combined or "work from home" in combined or "wfh" in combined:
        if "hybrid" in combined or "flexible" in combined or "2 days" in combined:
            return "Hybrid"
        return "Remote"
    if "hybrid" in combined or "flexible" in combined:
        return "Hybrid"
    return "Onsite"


def work_style_color(style):
    return {
        "Remote": "#61e6a6",
        "Hybrid": "#ffc857",
        "Onsite": "#ff8a65",
    }.get(style, "#91a7bc")


def source_badge_color(source):
    s = (source or "").lower()
    for key, color in SOURCE_COLORS.items():
        if key in s:
            return color
    return "#91a7bc"


# ── Card renderer ─────────────────────────────────────────────────────────

def render_card(job, stream_id):
    rid = role_id(job)
    score = job.get("score", 0)
    company = esc(job.get("company", ""))
    title = esc(job.get("title", ""))
    location = esc(job.get("location", ""))
    posted = relative_date(job.get("posted", ""))
    source = job.get("source", "")
    why = esc(job.get("why", ""))
    tags = job.get("tags", [])
    url = job.get("url", "#")
    work = work_style(job)
    work_color = work_style_color(work)
    src_color = source_badge_color(source)
    verification = job.get("listing_verification", "")
    route_type = job.get("application_route_type", "")

    tags_html = "".join(f'<span class="tag">{esc(t)}</span>' for t in tags[:4])

    # Score visual
    if score >= 85:
        score_cls = "score-high"
    elif score >= 70:
        score_cls = "score-mid"
    else:
        score_cls = "score-low"

    return f'''<article class="card" id="role-{rid}" data-role-id="{rid}" data-score="{score}" data-work="{work.lower()}" data-source="{source.lower()}" data-stream="{stream_id}">
  <div class="card-header">
    <a href="{esc(url)}" target="_blank" rel="noopener" class="card-title">{title}</a>
    <span class="score-badge {score_cls}">{score}%</span>
  </div>
  <div class="card-employer">{company}</div>
  <div class="card-badges">
    <span class="badge badge-work" style="color:{work_color};border-color:{work_color}">{work}</span>
    <span class="badge badge-source" style="color:{src_color};border-color:{src_color}">{esc(source)}</span>
    {f'<span class="badge badge-location">📍 {location}</span>' if location else ''}
    {f'<span class="badge badge-date">📅 {posted}</span>' if posted else ''}
  </div>
  {f'<p class="card-why">{why}</p>' if why else ''}
  {f'<div class="card-tags">{tags_html}</div>' if tags_html else ''}
  <div class="card-actions">
    <a href="{esc(url)}" target="_blank" rel="noopener" class="btn btn-apply" title="Open original listing">↗ Original</a>
    <button class="btn btn-pack" disabled title="Coming soon">⬇ Pack</button>
    <button class="btn btn-auto" disabled title="Coming soon">⚡ Auto-Apply</button>
    <span class="card-spacer"></span>
    <span class="stage-label">Stage:</span>
    <select class="status-select" data-role-id="{rid}" aria-label="Change application stage">
      <option>New</option><option>Review</option><option>Ready</option><option>Applied</option><option>Interview</option><option>Offer</option><option>Rejected</option>
    </select>
  </div>
</article>'''


# ── Stream section renderer ───────────────────────────────────────────────

def render_stream_section(stream_id, stream_info, jobs):
    if not jobs:
        return ""
    color = stream_info["color"]
    cards_html = "\n".join(render_card(j, stream_id) for j in jobs)
    return f'''<section class="stream-section" id="stream-{stream_id}" data-stream="{stream_id}">
  <div class="stream-header" style="border-color:{color}">
    <h2 style="color:{color}">{stream_info["icon"]} {stream_info["name"]} <span class="count-badge" style="color:{color};border-color:{color}">{len(jobs)}</span></h2>
    <p class="stream-desc">{stream_info["desc"]}</p>
  </div>
  <div class="grid">{cards_html}</div>
</section>'''


# ── HTML template ─────────────────────────────────────────────────────────

def build_page(streams, input_name, total_jobs):
    # Stats
    counts = {sid: len(jobs) for sid, jobs in streams.items()}
    all_sources = set()
    all_work_styles = set()
    for jobs in streams.values():
        for j in jobs:
            all_sources.add(j.get("source", ""))
            all_work_styles.add(work_style(j))

    # Filter option HTML
    source_options = "".join(
        f'<option value="{esc(s.lower())}">{esc(s)}</option>'
        for s in sorted(all_sources - {""})
    )
    work_options = "".join(
        f'<option value="{w.lower()}">{w}</option>'
        for w in sorted(all_work_styles - {""})
    )

    # Stream sections
    sections_html = "\n".join(
        render_stream_section(sid, STREAMS[sid], streams[sid])
        for sid in ["core-it", "bridge", "traineeship"]
        if streams[sid]
    )

    # Stream nav tabs
    tabs_html = "".join(
        f'<button class="tab" data-stream="{sid}" style="--tab-color:{STREAMS[sid]["color"]}">'
        f'{STREAMS[sid]["icon"]} {STREAMS[sid]["name"]} <span class="tab-count">{counts[sid]}</span></button>'
        for sid in ["core-it", "bridge", "traineeship"]
    )

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Job Dashboard — 3 Streams</title>
<style>
/* ── Reset & base ─────────────────────────────────── */
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;background:#0f0f23;color:#e0e0e0;line-height:1.5;min-height:100vh}}
a{{color:inherit;text-decoration:none}}

/* ── Layout ───────────────────────────────────────── */
.wrap{{max-width:1200px;margin:0 auto;padding:20px 24px 60px}}
.hero{{margin-bottom:24px}}
.hero h1{{font-size:1.6rem;font-weight:700;color:#fff;margin-bottom:4px}}
.hero p{{color:#888;font-size:.9rem}}

/* ── Stats bar ────────────────────────────────────── */
.stats{{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:20px}}
.stat{{background:#1a1a2e;border:1px solid #2a2a4a;border-radius:10px;padding:12px 20px;text-align:center;min-width:120px}}
.stat b{{display:block;font-size:1.3rem;color:#fff}}
.stat span{{font-size:.75rem;color:#888}}

/* ── Stream tabs ──────────────────────────────────── */
.tabs{{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:20px;border-bottom:1px solid #2a2a4a;padding-bottom:10px}}
.tab{{background:#1a1a2e;border:1px solid #2a2a4a;border-radius:8px;padding:8px 16px;color:#aaa;font-size:.85rem;cursor:pointer;transition:all .2s}}
.tab:hover{{border-color:var(--tab-color,#62d9ff);color:#fff}}
.tab.active{{background:color-mix(in srgb,var(--tab-color) 15%,#1a1a2e);border-color:var(--tab-color);color:#fff;font-weight:600}}
.tab-count{{display:inline-flex;align-items:center;justify-content:center;min-width:20px;height:20px;border-radius:999px;font-size:.7rem;font-weight:700;background:#0f0f23;border:1px solid var(--tab-color);padding:0 5px;margin-left:4px}}

/* ── Filters ──────────────────────────────────────── */
.filters{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:20px;align-items:center}}
.filters label{{font-size:.8rem;color:#888}}
.filters select{{background:#1a1a2e;border:1px solid #2a2a4a;border-radius:6px;color:#ddd;padding:5px 10px;font-size:.8rem}}
.filters select:focus{{outline:none;border-color:#62d9ff}}

/* ── Stream sections ──────────────────────────────── */
.stream-section{{margin-bottom:32px;display:none}}
.stream-section.visible{{display:block}}
.stream-header{{border-left:3px solid;padding:0 0 0 16px;margin-bottom:16px}}
.stream-header h2{{font-size:1.15rem;margin-bottom:2px}}
.stream-desc{{color:#888;font-size:.8rem}}
.count-badge{{display:inline-flex;align-items:center;justify-content:center;min-width:24px;height:24px;border-radius:999px;font-size:.75rem;font-weight:700;background:#0f0f23;border:1px solid;padding:0 6px;vertical-align:middle}}

/* ── Grid ─────────────────────────────────────────── */
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:14px}}

/* ── Card ─────────────────────────────────────────── */
.card{{background:#1a1a2e;border:1px solid #2a2a4a;border-radius:10px;padding:16px;transition:border-color .2s,box-shadow .2s;display:flex;flex-direction:column;gap:8px}}
.card:hover{{border-color:#3a3a5a;box-shadow:0 2px 12px rgba(0,0,0,.3)}}
.card.hidden{{display:none}}
.card-header{{display:flex;justify-content:space-between;align-items:flex-start;gap:8px}}
.card-title{{font-size:1rem;font-weight:600;color:#fff;flex:1;line-height:1.3}}
.card-title:hover{{color:#62d9ff}}
.card-employer{{font-size:.85rem;color:#aaa}}

/* Score badge */
.score-badge{{font-size:.75rem;font-weight:700;padding:2px 8px;border-radius:999px;white-space:nowrap;flex-shrink:0}}
.score-high{{background:#61e6a620;color:#61e6a6;border:1px solid #61e6a6}}
.score-mid{{background:#ffc85720;color:#ffc857;border:1px solid #ffc857}}
.score-low{{background:#ff6b6b20;color:#ff6b6b;border:1px solid #ff6b6b}}

/* Badges row */
.card-badges{{display:flex;gap:6px;flex-wrap:wrap}}
.badge{{font-size:.7rem;padding:2px 8px;border-radius:999px;border:1px solid;font-weight:500;white-space:nowrap}}

/* Why text */
.card-why{{font-size:.8rem;color:#999;font-style:italic}}

/* Tags */
.card-tags{{display:flex;gap:4px;flex-wrap:wrap}}
.tag{{font-size:.65rem;padding:2px 6px;border-radius:4px;background:#2a2a4a;color:#aaa}}

/* Actions row */
.card-actions{{display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-top:4px;border-top:1px solid #2a2a4a;padding-top:8px}}
.btn{{font-size:.75rem;padding:4px 10px;border-radius:6px;border:1px solid #3a3a5a;background:#0f0f23;color:#ccc;cursor:pointer;transition:all .15s}}
.btn:hover:not([disabled]){{border-color:#62d9ff;color:#fff}}
.btn[disabled]{{opacity:.35;cursor:not-allowed}}
.btn-apply{{border-color:#62d9ff;color:#62d9ff}}
.btn-apply:hover{{background:#62d9ff20}}
.card-spacer{{flex:1}}
.stage-label{{font-size:.75rem;color:#888}}
.status-select{{background:#0f0f23;border:1px solid #2a2a4a;border-radius:4px;color:#ccc;padding:3px 6px;font-size:.75rem}}

/* ── Footer ───────────────────────────────────────── */
.foot{{margin-top:40px;text-align:center;color:#555;font-size:.75rem;border-top:1px solid #2a2a4a;padding-top:16px}}

/* ── Responsive ───────────────────────────────────── */
@media(max-width:480px){{
  .grid{{grid-template-columns:1fr}}
  .stats{{flex-direction:column}}
}}
</style>
</head>
<body>
<div class="wrap">

<div class="hero">
  <h1>Job Dashboard</h1>
  <p>Stream-classified job listings with application tracking</p>
</div>

<section class="stats">
  <div class="stat"><b>{total_jobs}</b><span>Total Jobs</span></div>
  <div class="stat"><b>{counts.get("core-it",0)}</b><span>💻 Core IT</span></div>
  <div class="stat"><b>{counts.get("bridge",0)}</b><span>🌉 Bridge</span></div>
  <div class="stat"><b>{counts.get("traineeship",0)}</b><span>🔧 Traineeship</span></div>
</section>

<nav class="tabs" aria-label="Switch stream">
  <button class="tab active" data-stream="all" style="--tab-color:#fff">All <span class="tab-count">{total_jobs}</span></button>
  {tabs_html}
</nav>

<div class="filters">
  <label>Work Style:
    <select id="filter-work">
      <option value="all">All</option>
      {work_options}
    </select>
  </label>
  <label>Source:
    <select id="filter-source">
      <option value="all">All</option>
      {source_options}
    </select>
  </label>
</div>

{sections_html}

<div class="foot">Generated from {esc(input_name)} · {total_jobs} jobs across 3 streams</div>
</div>

<script>
(function() {{
  const STAGE_KEY = 'stage-';
  const stageOrder = ['New','Review','Ready','Applied','Interview','Offer','Rejected'];

  // ── Restore saved stages ──
  document.querySelectorAll('.status-select').forEach(sel => {{
    const rid = sel.dataset.roleId;
    const saved = localStorage.getItem(STAGE_KEY + rid);
    if (saved) sel.value = saved;
    sel.onchange = () => {{
      localStorage.setItem(STAGE_KEY + rid, sel.value);
    }};
  }});

  // ── Stream tab switching ──
  const tabs = document.querySelectorAll('.tab');
  const sections = document.querySelectorAll('.stream-section');

  function showStream(streamId) {{
    sections.forEach(s => {{
      if (streamId === 'all' || s.dataset.stream === streamId) {{
        s.classList.add('visible');
      }} else {{
        s.classList.remove('visible');
      }}
    }});
    tabs.forEach(t => {{
      t.classList.toggle('active', t.dataset.stream === streamId);
    }});
  }}

  tabs.forEach(t => {{
    t.onclick = () => showStream(t.dataset.stream);
  }});

  // Show all initially
  showStream('all');

  // ── Filters ──
  const filterWork = document.getElementById('filter-work');
  const filterSource = document.getElementById('filter-source');

  function applyFilters() {{
    const workVal = filterWork.value;
    const sourceVal = filterSource.value;
    document.querySelectorAll('.card').forEach(card => {{
      const matchWork = workVal === 'all' || card.dataset.work === workVal;
      const matchSource = sourceVal === 'all' || card.dataset.source === sourceVal;
      card.classList.toggle('hidden', !(matchWork && matchSource));
    }});
  }}

  filterWork.onchange = applyFilters;
  filterSource.onchange = applyFilters;
}})();
</script>
</body>
</html>'''


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    base = Path(__file__).parent

    # CLI argument or default
    if len(sys.argv) > 1:
        input_path = Path(sys.argv[1])
        if not input_path.is_absolute():
            input_path = base / input_path
    else:
        # Auto-detect: prefer combined, fall back to dated files
        candidates = [
            base / "scrapers" / "jobs_combined.json",
            base / "jobs_combined.json",
            base / "jobs_nonlinkedin_2026-08-23_final.json",
            base / "jobs_nonlinkedin_2026-08-22_final.json",
        ]
        input_path = None
        for c in candidates:
            if c.exists():
                input_path = c
                break
        if input_path is None:
            print("Error: no job data found. Provide a JSON file as argument.")
            sys.exit(1)

    print(f"Loading: {input_path}")
    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)

    jobs = data.get("jobs", [])
    if not jobs:
        print("Error: no jobs found in file")
        sys.exit(1)

    print(f"Classifying {len(jobs)} jobs into 3 streams...")
    streams = classify_all_jobs(jobs)

    # Print summary
    for sid, info in STREAMS.items():
        print(f"  {info['icon']} {info['name']}: {len(streams[sid])} jobs")

    # Build HTML
    output_path = base / "index.html"
    page = build_page(streams, input_path.name, len(jobs))
    output_path.write_text(page, encoding="utf-8")
    print(f"\nGenerated: {output_path}")
    print(f"  Total: {len(jobs)} jobs across 3 streams")


if __name__ == "__main__":
    main()
