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


def load_pack_index():
    """Load application_pack_index.json and build a lookup by URL."""
    base = Path(__file__).parent
    index_path = base / "application_pack_index.json"
    if not index_path.exists():
        return {}
    with open(index_path, encoding="utf-8") as f:
        data = json.load(f)
    packs = {}
    for role in data.get("roles", []):
        url = role.get("application_url") or role.get("application_route") or ""
        if url:
            packs[url] = role
    return packs

PACK_INDEX = load_pack_index()


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

    # Look up application pack
    pack = PACK_INDEX.get(url, {})
    resume_pdf = pack.get("resume", "")
    cover_pdf = pack.get("cover", "")
    email_md = pack.get("opening_email", "")

    tags_html = "".join(f'<span class="tag">{esc(t)}</span>' for t in tags[:4])

    # Score visual
    if score >= 85:
        score_cls = "score-high"
    elif score >= 70:
        score_cls = "score-mid"
    else:
        score_cls = "score-low"

    # Pack buttons
    pack_buttons = []
    if resume_pdf:
        pack_buttons.append(f'<a href="{esc(resume_pdf)}" download class="btn btn-pack" title="Download tailored resume (PDF)">⬇ Resume</a>')
    if cover_pdf:
        pack_buttons.append(f'<a href="{esc(cover_pdf)}" download class="btn btn-pack" title="Download cover letter (PDF)">⬇ Cover</a>')
    if email_md:
        pack_buttons.append(f'<a href="{esc(email_md)}" download class="btn btn-pack" title="Download opening email (MD)">⬇ Email</a>')
    if not pack_buttons:
        pack_buttons.append('<button class="btn btn-pack" disabled title="No pack available">⬇ Pack</button>')
    pack_html = " ".join(pack_buttons)

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
    {pack_html}
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
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
/* ── Reset & Base ─────────────────────────────────── */
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --bg-primary:#0a0a1a;
  --bg-secondary:#111128;
  --bg-card:#16163a;
  --bg-card-hover:#1c1c4a;
  --border:#252560;
  --border-hover:#3a3a8a;
  --text-primary:#f0f0ff;
  --text-secondary:#a0a0cc;
  --text-muted:#6060a0;
  --accent-blue:#62d9ff;
  --accent-green:#61e6a6;
  --accent-yellow:#ffc857;
  --accent-purple:#bda7ff;
  --accent-orange:#ff8a65;
  --accent-red:#ff6b6b;
  --glass-bg:rgba(22,22,58,0.7);
  --glass-border:rgba(100,100,200,0.15);
  --shadow-sm:0 2px 8px rgba(0,0,0,0.3);
  --shadow-md:0 4px 20px rgba(0,0,0,0.4);
  --shadow-lg:0 8px 40px rgba(0,0,0,0.5);
  --radius-sm:8px;
  --radius-md:12px;
  --radius-lg:16px;
  --radius-full:999px;
}}
body{{
  font-family:'Inter',-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  background:var(--bg-primary);
  color:var(--text-primary);
  line-height:1.6;
  min-height:100vh;
  background-image:
    radial-gradient(ellipse 80% 50% at 50% -20%,rgba(98,217,255,0.08),transparent),
    radial-gradient(ellipse 60% 40% at 80% 100%,rgba(189,167,255,0.06),transparent);
}}
a{{color:inherit;text-decoration:none}}

/* ── Layout ───────────────────────────────────────── */
.wrap{{max-width:1280px;margin:0 auto;padding:32px 28px 80px}}

/* ── Hero ─────────────────────────────────────────── */
.hero{{margin-bottom:32px;position:relative}}
.hero h1{{
  font-size:2rem;font-weight:800;color:var(--text-primary);
  letter-spacing:-0.03em;
  background:linear-gradient(135deg,#fff 0%,var(--accent-blue) 100%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  background-clip:text;
}}
.hero p{{color:var(--text-muted);font-size:.9rem;margin-top:4px}}

/* ── Stats Bar ────────────────────────────────────── */
.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:28px}}
.stat{{
  background:var(--glass-bg);
  backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);
  border:1px solid var(--glass-border);
  border-radius:var(--radius-md);
  padding:16px 20px;
  text-align:center;
  transition:all .25s ease;
  position:relative;
  overflow:hidden;
}}
.stat::before{{
  content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,transparent,var(--accent-blue),transparent);
  opacity:0;transition:opacity .25s;
}}
.stat:hover::before{{opacity:1}}
.stat:hover{{border-color:var(--border-hover);transform:translateY(-2px);box-shadow:var(--shadow-md)}}
.stat b{{display:block;font-size:1.5rem;font-weight:700;color:#fff;margin-bottom:2px}}
.stat span{{font-size:.75rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:.05em;font-weight:500}}

/* ── Tabs ─────────────────────────────────────────── */
.tabs{{
  display:flex;gap:8px;flex-wrap:wrap;margin-bottom:24px;
  padding-bottom:16px;border-bottom:1px solid var(--border);
}}
.tab{{
  background:var(--bg-secondary);
  border:1px solid var(--border);
  border-radius:var(--radius-full);
  padding:10px 20px;
  color:var(--text-secondary);
  font-size:.85rem;font-weight:500;
  cursor:pointer;
  transition:all .2s ease;
  display:flex;align-items:center;gap:6px;
}}
.tab:hover{{
  border-color:var(--tab-color,#62d9ff);
  color:#fff;
  box-shadow:0 0 20px rgba(98,217,255,0.1);
}}
.tab.active{{
  background:color-mix(in srgb,var(--tab-color) 15%,var(--bg-secondary));
  border-color:var(--tab-color);
  color:#fff;font-weight:600;
  box-shadow:0 0 24px rgba(98,217,255,0.15);
}}
.tab-count{{
  display:inline-flex;align-items:center;justify-content:center;
  min-width:22px;height:22px;border-radius:var(--radius-full);
  font-size:.7rem;font-weight:700;
  background:var(--bg-primary);
  border:1px solid var(--tab-color);
  padding:0 6px;
}}

/* ── Filters ──────────────────────────────────────── */
.filters{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:24px;align-items:center}}
.filters label{{font-size:.8rem;color:var(--text-muted);font-weight:500}}
.filters select{{
  background:var(--bg-secondary);
  border:1px solid var(--border);
  border-radius:var(--radius-sm);
  color:var(--text-primary);
  padding:8px 12px;
  font-size:.8rem;
  font-family:inherit;
  cursor:pointer;
  transition:all .2s;
}}
.filters select:hover{{border-color:var(--border-hover)}}
.filters select:focus{{outline:none;border-color:var(--accent-blue);box-shadow:0 0 0 3px rgba(98,217,255,0.15)}}

/* ── Stream Sections ──────────────────────────────── */
.stream-section{{margin-bottom:36px;display:none}}
.stream-section.visible{{display:block}}
.stream-header{{
  border-left:3px solid;padding:0 0 0 20px;margin-bottom:20px;
}}
.stream-header h2{{font-size:1.25rem;font-weight:700;margin-bottom:4px}}
.stream-desc{{color:var(--text-muted);font-size:.85rem}}
.count-badge{{
  display:inline-flex;align-items:center;justify-content:center;
  min-width:26px;height:26px;border-radius:var(--radius-full);
  font-size:.75rem;font-weight:700;
  background:var(--bg-primary);border:1px solid;
  padding:0 8px;vertical-align:middle;margin-left:8px;
}}

/* ── Grid ─────────────────────────────────────────── */
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(360px,1fr));gap:16px}}

/* ── Card ─────────────────────────────────────────── */
.card{{
  background:var(--glass-bg);
  backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);
  border:1px solid var(--glass-border);
  border-radius:var(--radius-lg);
  padding:20px;
  transition:all .25s ease;
  display:flex;flex-direction:column;gap:10px;
  position:relative;
  overflow:hidden;
}}
.card::after{{
  content:'';position:absolute;top:0;left:0;right:0;height:1px;
  background:linear-gradient(90deg,transparent,rgba(98,217,255,0.3),transparent);
  opacity:0;transition:opacity .25s;
}}
.card:hover{{
  border-color:var(--border-hover);
  box-shadow:var(--shadow-lg);
  transform:translateY(-2px);
}}
.card:hover::after{{opacity:1}}
.card.hidden{{display:none}}

.card-header{{display:flex;justify-content:space-between;align-items:flex-start;gap:10px}}
.card-title{{
  font-size:1rem;font-weight:600;color:#fff;flex:1;line-height:1.35;
  transition:color .2s;
}}
.card-title:hover{{color:var(--accent-blue)}}
.card-employer{{font-size:.85rem;color:var(--text-secondary);font-weight:500}}

/* Score badge */
.score-badge{{
  font-size:.75rem;font-weight:700;
  padding:4px 10px;border-radius:var(--radius-full);
  white-space:nowrap;flex-shrink:0;
  backdrop-filter:blur(8px);
}}
.score-high{{background:rgba(97,230,166,0.15);color:var(--accent-green);border:1px solid rgba(97,230,166,0.3)}}
.score-mid{{background:rgba(255,200,87,0.15);color:var(--accent-yellow);border:1px solid rgba(255,200,87,0.3)}}
.score-low{{background:rgba(255,107,107,0.1);color:var(--accent-red);border:1px solid rgba(255,107,107,0.2)}}

/* Badges row */
.card-badges{{display:flex;gap:6px;flex-wrap:wrap}}
.badge{{
  font-size:.7rem;padding:3px 10px;border-radius:var(--radius-full);
  border:1px solid;font-weight:500;white-space:nowrap;
  backdrop-filter:blur(4px);
}}

/* Why text */
.card-why{{font-size:.82rem;color:var(--text-muted);font-style:italic;line-height:1.5}}

/* Tags */
.card-tags{{display:flex;gap:4px;flex-wrap:wrap}}
.tag{{
  font-size:.65rem;padding:3px 8px;border-radius:var(--radius-sm);
  background:rgba(37,37,96,0.6);color:var(--text-muted);
  border:1px solid rgba(100,100,200,0.1);
  transition:all .2s;
}}
.tag:hover{{background:rgba(50,50,120,0.8);color:var(--text-secondary)}}

/* Actions row */
.card-actions{{
  display:flex;align-items:center;gap:6px;flex-wrap:wrap;
  margin-top:6px;border-top:1px solid rgba(100,100,200,0.1);
  padding-top:12px;
}}
.btn{{
  font-size:.75rem;font-weight:500;
  padding:6px 12px;border-radius:var(--radius-sm);
  border:1px solid var(--border);
  background:var(--bg-primary);
  color:var(--text-secondary);
  cursor:pointer;
  transition:all .2s ease;
  font-family:inherit;
}}
.btn:hover:not([disabled]){{
  border-color:var(--accent-blue);
  color:#fff;
  box-shadow:0 0 12px rgba(98,217,255,0.15);
}}
.btn[disabled]{{opacity:.35;cursor:not-allowed}}
.btn-apply{{border-color:var(--accent-blue);color:var(--accent-blue)}}
.btn-apply:hover{{background:rgba(98,217,255,0.1)}}
.card-spacer{{flex:1}}
.stage-label{{font-size:.75rem;color:var(--text-muted);font-weight:500}}
.status-select{{
  background:var(--bg-primary);
  border:1px solid var(--border);
  border-radius:var(--radius-sm);
  color:var(--text-secondary);
  padding:5px 8px;
  font-size:.75rem;
  font-family:inherit;
  cursor:pointer;
  transition:all .2s;
}}
.status-select:hover{{border-color:var(--border-hover)}}
.status-select:focus{{outline:none;border-color:var(--accent-blue)}}

/* ── Footer ───────────────────────────────────────── */
.foot{{
  margin-top:48px;text-align:center;color:var(--text-muted);
  font-size:.75rem;
  border-top:1px solid var(--border);
  padding-top:20px;
}}

/* ── Responsive ───────────────────────────────────── */
@media(max-width:768px){{
  .stats{{grid-template-columns:repeat(2,1fr)}}
  .grid{{grid-template-columns:1fr}}
  .hero h1{{font-size:1.5rem}}
}}
@media(max-width:480px){{
  .stats{{grid-template-columns:1fr}}
  .tabs{{gap:6px}}
  .tab{{padding:8px 14px;font-size:.8rem}}
  .wrap{{padding:20px 16px 60px}}
}}

/* ── Animations ───────────────────────────────────── */
@keyframes fadeIn{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:translateY(0)}}}}
.card{{animation:fadeIn .3s ease both}}
.grid .card:nth-child(1){{animation-delay:.05s}}
.grid .card:nth-child(2){{animation-delay:.1s}}
.grid .card:nth-child(3){{animation-delay:.15s}}
.grid .card:nth-child(4){{animation-delay:.2s}}
.grid .card:nth-child(5){{animation-delay:.25s}}
.grid .card:nth-child(6){{animation-delay:.3s}}
.grid .card:nth-child(7){{animation-delay:.35s}}
.grid .card:nth-child(8){{animation-delay:.4s}}
.grid .card:nth-child(9){{animation-delay:.45s}}
.grid .card:nth-child(10){{animation-delay:.5s}}
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

def build_dashboard(input_file=None, output_file=None):
    """Build dashboard from a JSON file. Callable from other scripts."""
    base = Path(__file__).parent

    if input_file:
        input_path = Path(input_file)
        if not input_path.is_absolute():
            input_path = base / input_path
    else:
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
            print("Error: no job data found.")
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

    for sid, info in STREAMS.items():
        print(f"  {info['icon']} {info['name']}: {len(streams[sid])} jobs")

    if output_file:
        out = Path(output_file)
    else:
        out = base / "index.html"

    page = build_page(streams, input_path.name, len(jobs))
    out.write_text(page, encoding="utf-8")
    print(f"Generated: {out}")
    return str(out)


def main():
    build_dashboard()


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
