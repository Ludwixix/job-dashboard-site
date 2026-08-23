#!/usr/bin/env python3
"""Relevance re-scorer for Sam's job dashboard.

Pure stdlib, idempotent, non-destructive. Reads a jobs JSON, scores each
listing against Sam's documented stack (resume.md source of truth), re-buckets
noisy categories, emits shortlist JSON + Markdown.

Outputs (all under ./pipeline-demo/):
  03-shortlist.json   ranked shortlist with per-role match reasons
  03-shortlist.md     Markdown summary
"""

import json
import re
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent

# ---------------------------------------------------------------- source of truth
# Sam's documented stack (from resume.md / shared voice guide) — title-weighted.
# (skill, weight) tuples. Title gets 3x, description 2x, tags/why 1x.
PROFILE = {
    # core M365 / identity / endpoint
    "m365": 5, "entra": 5, "azure ad": 5, "intune": 5, "autopilot": 4,
    "sharepoint": 5, "office 365": 4, "outlook": 3, "exchange": 3,
    "servicenow": 5, "itil": 4, "powershell": 5, "microsoft": 3,
    # endpoint / infra
    "endpoint": 5, "windows": 4, "windows 11": 4, "sysadmin": 4,
    "system administrator": 4, "infrastructure": 3, "active directory": 4,
    "configuration management": 3, "deployment": 3, "imaging": 3,
    # service desk
    "helpdesk": 4, "help desk": 4, "service desk": 4, "tier 2": 4,
    "level 2 support": 4, "it support": 4, "l2 support": 4, "tier 3": 3,
    # cloud / devops / automation
    "azure": 4, "cloud": 3, "devops": 3, "automation": 4, "python": 3,
    # security (adjacent)
    "security": 2, "iam": 3,
}

# Hard exclusions: roles in a different engineering discipline entirely.
NON_IT_MARKERS = [
    "electrical", "power systems", "civil", "mechanical", "structural",
    "underwriter", "insurance", "litigation", "legal assistant", "concierge",
    "duty manager", "merchandising", "marketing", "sales &",
    "talent acquisition", "nurse", "attendant", "nursing", "pharmacy",
    "chef", "hospitality", "accountant", "finance", "underwriter",
]

# Role-function guardrails: keyword-rich titles that are NOT engineering roles.
ROLE_NEGATIVES = [
    "sales", "account manager", "specialist", "business development",
    "pre-sales", "customer success", "relationship manager", "partner",
    "recruiter", "consultant (sales", "quota", "evangelist",
]

# Staffing / aggregator firms: re-list roles, add no signal.
STAFFING_FIRMS = [
    "xpt software", "milestone it", "hastha", "hays", "randstad",
    "robert half", "talent intl", "halcyon knights", "congruence",
    "deliver", "indeed", "adzuna",
]


def text_of(job):
    return " ".join([
        job.get("title", ""),
        " ".join(job.get("tags", [])),
        job.get("why", ""),
        job.get("location", ""),
    ]).lower()


def score_job(job_iter):
    results = []
    for j in job_iter:
        title = (j.get("title", "") or "").lower()
        desc = (j.get("description") or "").lower()
        tagwhy = (" ".join((j.get("tags") or [])) + " " + (j.get("why") or "")).lower()

        s = 0.0
        reasons = []
        for term, w in PROFILE.items():
            counted = 0
            if term in title:
                counted += 3
            if term in desc:
                counted += 2
            if term in tagwhy:
                counted += 1
            if counted:
                contributed = w * counted
                s += contributed
                reasons.append((term, counted, contributed))

        # role-function guardrail: even with azure/microsoft keywords,
        # a sales/specialist/bd title is not what Sam applies to
        if any(m in title for m in ROLE_NEGATIVES):
            s *= 0.3

        # staffing-firm flag (visibility only, no penalty)
        staffing = any(f in (j.get("company") or "").lower() for f in STAFFING_FIRMS)

        # low-signal flag (missing / short description)
        low_signal = len(desc) < 200

        results.append({
            "title": j.get("title"),
            "company": j.get("company"),
            "location": j.get("location"),
            "source": j.get("source"),
            "salary": j.get("salary", ""),
            "url": j.get("url"),
            "subcategory": j.get("subcategory"),
            "score": round(s, 1),
            "low_signal": low_signal,
            "staffing_firm": staffing,
            "reasons": reasons[:6],
        })

    # dedupe by normalized (title, company) — keep the higher score
    seen = set()
    deduped = []
    for r in sorted(results, key=lambda x: -x["score"]):
        key = (r["title"].lower().strip(), (r["company"] or "").lower().strip())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(r)

    deduped.sort(key=lambda x: -x["score"])
    return deduped


def load_jobs():
    candidates = sorted(REPO.glob("jobs_nonlinkedin_*_final.json"))
    if not candidates:
        sys.exit("No jobs JSON found")
    path = candidates[-1]
    with open(path) as fh:
        data = json.load(fh)
    return path, data.get("jobs", [])


def write_outputs(path, results):
    out_dir = HERE
    top = [r | {"reason_text": ", ".join(str(t) for t, _, _ in r["reasons"])} for r in results[:20]]
    (out_dir / "03-shortlist.json").write_text(
        json.dumps(top, indent=1), encoding="utf-8"
    )

    lines = [
        "# Job Re-Score Shortlist",
        "",
        f"Source: {path.name}",
        f"Jobs ranked: {len(results)} (after dedupe)",
        "",
        "Legend: ⚠️=low-signal (missing/short description) · 🏢=staffing/aggregator firm",
        "",
        "| # | Title | Company | Location | Score | Flags | Match |",
        "|---|-------|---------|----------|-------|-------|-------|",
    ]
    for i, r in enumerate(top[:15], 1):
        reason = r["reason_text"] or "(no strong match)"
        flags = "⚠️" * r.get("low_signal", False) + "🏢" * r.get("staffing_firm", False)
        lines.append(f"| {i} | {r['title']} | {r['company']} | {r['location']} | {r['score']:.0f} | {flags} | {reason[:50]} |")
    (out_dir / "03-shortlist.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote 03-shortlist.json / 03-shortlist.md")


if __name__ == "__main__":
    path, jobs = load_jobs()
    results = score_job(jobs)
    write_outputs(path, results)