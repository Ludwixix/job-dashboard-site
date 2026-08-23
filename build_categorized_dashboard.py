#!/usr/bin/env python3
"""Generate a category-grouped job dashboard from clean JSON data.

Displays jobs organized by IT subcategory with proper visual separation.
Each category shows its own grid with a header, badge count, and description.
"""
import html as html_mod
import json
import hashlib
import re
import sys
from pathlib import Path

# ── Category definitions ──────────────────────────────────────────────────
CATEGORIES = {
    "cloud-devops": {
        "name": "Cloud & DevOps",
        "color": "#62d9ff",
        "icon": "☁️",
        "desc": "Cloud platforms, DevOps, SRE, Azure/AWS, infrastructure automation, containerisation",
    },
    "security": {
        "name": "Security & Cyber",
        "color": "#ff6b6b",
        "icon": "🛡️",
        "desc": "SOC, cyber security, compliance, penetration testing, vulnerability management",
    },
    "m365-identity": {
        "name": "M365, Identity & Endpoint",
        "color": "#bda7ff",
        "icon": "🔐",
        "desc": "Entra ID, Intune, MDM, EUC, modern workplace, identity management",
    },
    "service-desk": {
        "name": "Service Desk & Support",
        "color": "#ffc857",
        "icon": "🎧",
        "desc": "L1/L2/L3 help desk, desktop support, IT support, technical support",
    },
    "infrastructure-systems": {
        "name": "Infrastructure & Systems",
        "color": "#61e6a6",
        "icon": "🖥️",
        "desc": "Sysadmin, networking, servers, data centre, virtualisation, Windows/Linux",
    },
    "software-data": {
        "name": "Software & Data",
        "color": "#ff8a65",
        "icon": "💻",
        "desc": "Software engineering, data engineering, AI/ML, full-stack development",
    },
    "project-management": {
        "name": "Project & IT Management",
        "color": "#91a7bc",
        "icon": "📋",
        "desc": "PM, BA, delivery, agile, scrum, service management, change management",
    },
}

# ── HTML helpers ──────────────────────────────────────────────────────────
def esc(text):
    return html_mod.escape(str(text))


def role_id(job):
    route = job.get("application_route") or job.get("url") or ""
    return hashlib.sha256(route.encode()).hexdigest()[:12]


def stage_class(status):
    return f"stage-{(status or 'new').lower()}"


def render_card(job, category_id=None):
    """Render a single job card."""
    rid = role_id(job)
    score = job.get("score", 0)
    company = esc(job.get("company", ""))
    title = esc(job.get("title", ""))
    location = esc(job.get("location", ""))
    posted = job.get("posted", "")
    source = job.get("source", "")
    why = esc(job.get("why", ""))
    tags = job.get("tags", [])
    url = job.get("url", "#")
    work = "remote" if job.get("remote") else "onsite"
    verification = "verified" if "verified" in (job.get("listing_verification") or "").lower() else "review"
    route_type = job.get("application_route_type", "")

    tags_html = "".join(f'<span class="tag">{esc(t)}</span>' for t in tags[:5])
    score_cls = "score" if score >= 85 else "flag" if score < 70 else ""

    return f'''<article class="card stage-new" id="role-{rid}" data-role-id="{rid}" data-score="{score}" data-work="{work}" data-source="{source.lower()}" data-source-group="{source.lower()}" data-verification="{verification}" data-lane="core" data-category="{category_id or ''}">
<div class="rank">#{job.get("rank", "?")} · {score}% SCREENING MATCH</div>
<div class="company">{company}</div>
<div class="title">{title}</div>
<div class="meta"><span>📍 {location}</span><span>📅 Posted {posted}</span><span>🔎 {esc(source)}</span><span>🧭 {esc(route_type)}</span></div>
<p class="why">{why}</p>
<div class="tags"><span class="tag score">{score} screening match</span>{tags_html}</div>
<div class="role-controls"><span class="stage-label">Stage: <b class="stage-value" data-role-id="{rid}">New</b></span>
<select class="status-select" data-role-id="{rid}" aria-label="Change application stage">
<option>New</option><option>Review</option><option>Ready</option><option>Applied</option><option>Interview</option><option>Offer</option><option>Rejected</option>
</select>
<button class="copy-link-btn" data-role-id="{rid}" title="Copy a direct link to this role">Copy link</button></div>
<div class="links">
<a class="primary-link" href="{esc(url)}" target="_blank" rel="noopener">↗ Apply / open route</a></div>
</article>'''


def render_category_section(cat_id, cat_info, jobs):
    """Render a full category section with header and card grid."""
    count = len(jobs)
    color = cat_info["color"]
    cards_html = "\n".join(render_card(j, cat_id) for j in jobs)

    return f'''<section class="lane category-section" id="cat-{cat_id}" style="border-left:3px solid {color};padding-left:18px;margin:20px 0">
<h2 style="color:{color};font-size:20px;margin:0 0 4px">{cat_info["icon"]} {cat_info["name"]} <span class="category-badge" style="color:{color};border-color:{color}">{count}</span></h2>
<p style="color:var(--muted);margin:0 0 14px;font-size:13px">{cat_info["desc"]}</p>
<div class="grid">{cards_html}</div>
</section>'''


def render_other_section(jobs):
    """Render the non-IT / other jobs section."""
    if not jobs:
        return ""
    cards_html = "\n".join(render_card(j, "other") for j in jobs)
    return f'''<section class="lane outdoor" id="other-jobs" style="border-top:3px solid #61e6a6">
<h2>🌿 Other Jobs ({len(jobs)})</h2>
<p style="color:var(--muted);margin:0 0 14px">Non-IT roles: outdoor, trades, hospitality, admin, and other positions.</p>
<div class="grid">{cards_html}</div>
</section>'''


def render_section_lane(section_name, section_label, icon, color, jobs):
    """Render a section (technician, outdoor, local, linkedin)."""
    if not jobs:
        return ""
    cards_html = "\n".join(render_card(j, section_name) for j in jobs)
    return f'''<section class="lane {section_name}" id="{section_name}-jobs" style="border-top:3px solid {color}">
<h2>{icon} {section_label} ({len(jobs)})</h2>
<div class="grid">{cards_html}</div>
</section>'''


# ── Main ──────────────────────────────────────────────────────────────────
def main():
    base = Path(__file__).parent
    input_path = base / "jobs_nonlinkedin_2026-08-23_final.json"
    css_path = base / "_style.css"
    output_path = base / "index_categorized.html"

    if not input_path.exists():
        input_path = base / "jobs_nonlinkedin_2026-08-08_reclassified.json"
    if not input_path.exists():
        print(f"Error: no job data found")
        sys.exit(1)

    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)

    # Load CSS
    css = css_path.read_text(encoding="utf-8") if css_path.exists() else ""

    # Separate core jobs by subcategory
    core_jobs = data.get("jobs", [])
    cat_jobs = {cat_id: [] for cat_id in CATEGORIES}
    other_jobs = []

    for job in core_jobs:
        subcat = job.get("subcategory", "")
        if subcat in CATEGORIES:
            cat_jobs[subcat].append(job)
        else:
            other_jobs.append(job)

    # Sections
    sections = data.get("sections", {})

    # Build HTML
    stats_total = len(core_jobs)
    stats_it = sum(len(v) for v in cat_jobs.values())
    stats_other = len(other_jobs)

    category_html = "\n".join(
        render_category_section(cat_id, cat_info, cat_jobs[cat_id])
        for cat_id, cat_info in CATEGORIES.items()
        if cat_jobs[cat_id]
    )

    other_html = render_other_section(other_jobs)

    tech_html = render_section_lane("technician", "Technician & Trade", "🔧", "#bda7ff", sections.get("technician", []))
    outdoor_html = render_section_lane("outdoor", "Outdoor & Council", "🌿", "#61e6a6", sections.get("outdoor", []))
    local_html = render_section_lane("local", "Local & Support Near St Kilda", "📍", "#ffc857", sections.get("local", []))
    linkedin_html = render_section_lane("linkedin", "LinkedIn Listings", "💼", "#0a66c2", sections.get("linkedin", []))

    page = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sam Ludwig — Job Dashboard</title>
<style>{css}</style>
<style>
.category-section {{ background: linear-gradient(145deg, var(--panel), #0e192a); border: 1px solid var(--line); border-radius: 14px; padding: 20px; }}
.category-badge {{ display: inline-flex; align-items: center; justify-content: center; min-width: 28px; height: 28px; border-radius: 999px; font-size: 13px; font-weight: 700; padding: 0 8px; background: #0b1727; border: 1px solid currentColor; }}
.category-nav {{ display: flex; gap: 8px; flex-wrap: wrap; margin: 0 0 22px; }}
.category-nav a {{ color: var(--cyan); text-decoration: none; border: 1px solid var(--line); border-radius: 999px; padding: 7px 14px; background: #0d192a; font-size: 13px; }}
.category-nav a:hover {{ border-color: var(--cyan); }}
</style>
</head>
<body>
<div class="wrap">
<div class="hero">
<div>
<div class="eyebrow">Job Dashboard</div>
<h1>Sam Ludwig — St Kilda Job Dashboard</h1>
<p>Categorized job listings with screening scores and application tracking.</p>
</div>
</div>

<section class="stats">
<div class="stat"><b>{stats_it}</b><span>IT jobs (categorized)</span></div>
<div class="stat"><b>{stats_other}</b><span>Other roles</span></div>
<div class="stat"><b>{len(sections.get("local", []))}</b><span>Local to St Kilda</span></div>
<div class="stat"><b>{len(sections.get("linkedin", []))}</b><span>LinkedIn listings</span></div>
</section>

<nav class="category-nav" aria-label="Jump to category">
{''.join(f'<a href="#cat-{cat_id}">{cat_info["icon"]} {cat_info["name"]} ({len(cat_jobs[cat_id])})</a>' for cat_id, cat_info in CATEGORIES.items() if cat_jobs[cat_id])}
<a href="#other-jobs">🌿 Other ({stats_other})</a>
<a href="#technician-jobs">🔧 Technician ({len(sections.get("technician", []))})</a>
<a href="#outdoor-jobs">🌿 Outdoor ({len(sections.get("outdoor", []))})</a>
<a href="#local-jobs">📍 Local ({len(sections.get("local", []))})</a>
<a href="#linkedin-jobs">💼 LinkedIn ({len(sections.get("linkedin", []))})</a>
</nav>

{category_html}
{other_html}
{tech_html}
{outdoor_html}
{local_html}
{linkedin_html}

<div class="foot">Generated from {input_path.name} · {stats_total} IT jobs categorized into {sum(1 for v in cat_jobs.values() if v)} subcategories</div>
</div>

<script>
/* Stage persistence via localStorage */
const stageOrder = ['New','Review','Ready','Applied','Interview','Offer','Rejected'];
document.querySelectorAll('.status-select').forEach(select => {{
    const rid = select.dataset.roleId;
    const saved = localStorage.getItem('stage-' + rid);
    if (saved) {{ select.value = saved; }}
    select.onchange = () => {{
        localStorage.setItem('stage-' + rid, select.value);
        const value = document.querySelector(`.stage-value[data-role-id="${{rid}}"]`);
        if (value) value.textContent = select.value;
    }};
}});
/* Copy link */
document.querySelectorAll('.copy-link-btn').forEach(btn => {{
    btn.onclick = async () => {{
        const url = `${{location.origin}}${{location.pathname}}#role-${{btn.dataset.roleId}}`;
        try {{ await navigator.clipboard.writeText(url); btn.textContent = 'Copied'; setTimeout(() => btn.textContent = 'Copy link', 1400); }}
        catch {{ prompt('Copy this link:', url); }}
    }};
}});
/* Smooth scroll for category nav */
document.querySelectorAll('.category-nav a').forEach(a => {{
    a.onclick = (e) => {{
        e.preventDefault();
        document.querySelector(a.getAttribute('href'))?.scrollIntoView({{ behavior: 'smooth' }});
    }};
}});
</script>
</body>
</html>'''

    output_path.write_text(page, encoding="utf-8")
    print(f"Generated {output_path.name}")
    print(f"  IT jobs: {stats_it} in {sum(1 for v in cat_jobs.values() if v)} categories")
    for cat_id, jobs in cat_jobs.items():
        if jobs:
            print(f"    {CATEGORIES[cat_id]['name']}: {len(jobs)}")
    print(f"  Other: {stats_other}")
    print(f"  Sections: technician={len(sections.get('technician',[]))}, outdoor={len(sections.get('outdoor',[]))}, local={len(sections.get('local',[]))}, linkedin={len(sections.get('linkedin',[]))}")


if __name__ == "__main__":
    main()
