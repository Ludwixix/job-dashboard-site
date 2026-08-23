#!/usr/bin/env python3
"""
generate_packs_batch.py — Concurrent DeepSeek (OpenRouter) generator for all jobs.

For each role in scrapers/jobs_combined.json, call the LLM to write a tailored
resume + cover letter from the REAL verified resume/profile (no fabrication).
Outputs markdown into applications/ with the same naming the dashboard expects
(<company>_<title>_resume.md / _cover_letter.md), so 📄 Download buttons appear.

Run: python3 generate_packs_batch.py
"""
import concurrent.futures
import json
import os
import re
import sys
import time
import urllib.request
import argparse
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "scrapers" / "jobs_combined.json"
APP = ROOT / "applications"
APP.mkdir(exist_ok=True)

# Prevent concurrent duplicate runs (e.g. after a gateway restart)
LOCK = ROOT / ".packs_batch.lock"
import os as _os
if LOCK.exists():
    raise SystemExit("Another batch run is active (.packs_batch.lock exists). Remove it if stale.")
LOCK.write_text(str(_os.getpid()), encoding="utf-8")

import atexit
def _release_lock():
    try:
        LOCK.unlink()
    except FileNotFoundError:
        pass
atexit.register(_release_lock)

# Pull the OpenRouter key from OpenClaw's local config (never printed).
KEY = None
try:
    cfg = json.load(open("/home/s/.openclaw/openclaw.json", encoding="utf-8"))
    for m in re.finditer(r'"(sk-or-v1-[^"]+)"', json.dumps(cfg)):
        KEY = m.group(1)
except Exception:
    pass
if not KEY:
    raise SystemExit("No OPENROUTER key found in /home/s/.openclaw/openclaw.json")

MODEL = os.environ.get("LLM_MODEL", "deepseek/deepseek-v4-flash-0731")
MAX_WORKERS = int(os.environ.get("PACK_WORKERS", "2"))
TIMEOUT = 420
MAX_RETRIES = 3

RESUME = (ROOT / "resume.md").read_text(encoding="utf-8")
PROFILE = (ROOT / "job_profile.json").read_text(encoding="utf-8")

SYSTEM = """You are a senior Australian recruitment specialist producing a tailored
résumé and cover letter in Markdown from the candidate's REAL, VERIFIED work history ONLY.

ABSOLUTE RULES:
- NEVER fabricate employers, titles, dates, qualifications, licences, security
  clearances, vehicle access, RSA, tools, or skills not present in the candidate profile.
- Tailor/re-order REAL experience and skills to match the role. No invented achievements.
- Résumé: clean Markdown with ## headings and - bullets. Reorder skills/experience so the
  most role-relevant appear first. No email/phone identity block at top (header is drawn
  by the page).
- Cover letter: 3-4 short, human paragraphs referencing the company, role title, location,
  and 2-3 genuinely matched wins. Australian spelling (organise, licence).
- Separate the two documents ONLY with the single line: ===COVER_LETTER===
- After the cover letter, add ONE more section starting with the line: ===JOB_DESCRIPTION===
  In 3-5 crisp sentences, write an in-depth summary of the role (responsibilities, key
  requirements, technologies) based on the role description and your reading of the
  listing — still factual, no invented specifics beyond what the posting implies.
  This is displayed on the dashboard card, so make it informative and skimmable."""


def clean(s):
    s = (s or "").lower().replace("&", "and").replace("—", "-")
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s[:95]


def call_llm(messages):
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.4,
        "max_tokens": 3000,
    }
    last = None
    for attempt in range(1, MAX_RETRIES + 1):
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {KEY}"},
        )
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                data = json.loads(resp.read())
            content = data.get("choices", [{}])[0].get("message", {}).get("content")
            if content and content.strip():
                return content, time.time() - t0
            last = f"empty content: {json.dumps(data)[:300]}"
        except Exception as e:
            last = f"{type(e).__name__}: {e}"
        if attempt < MAX_RETRIES:
            wait = 10 * attempt
            print(f"  retry {attempt}: {last} (wait {wait}s)", flush=True)
            time.sleep(wait)
    raise RuntimeError(f"LLM failed after {MAX_RETRIES} attempts: {last}")


def process_job(job):
    title = job.get("title", "")
    company = job.get("company", "")
    description = (job.get("description") or "")[:900]
    why = job.get("why", "")
    location = job.get("location", "")

    user = f"""Candidate master résumé (VERIFIED FACT ONLY):
{RESUME[:6000]}

Candidate profile JSON:
{PROFILE}

=== TARGET ROLE ===
Title: {title}
Company: {company}
Location: {location}
Why flagged: {why}

Role description:
{description}

Produce TWO Markdown documents separated exactly by the single line: ===COVER_LETTER===
Résumé first (## headings, - bullets, no identity block), then the separator
line, then the cover letter (## Cover Letter, 3-4 paragraphs, company-aware)."""

    content, dt = call_llm([
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user},
    ])
    return content, dt, title, company, description, why, location


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="Only generate first N jobs (0 = all)")
    args = ap.parse_args()

    data = json.loads(DATA.read_text(encoding="utf-8"))
    jobs = data.get("jobs", [])
    if args.limit:
        jobs = jobs[: args.limit]

    # Resume: skip any job whose pack markdown already exists
    todo = []
    for j in jobs:
        prefix = f"{clean(j.get('company',''))}_{clean(j.get('title',''))}"
        if (APP / f"{prefix}_resume.md").exists() and (APP / f"{prefix}_cover_letter.md").exists():
            continue
        todo.append(j)
    skipped = len(jobs) - len(todo)
    if skipped:
        print(f"[packs] Skipping {skipped} already-generated jobs; {len(todo)} to do", flush=True)
    jobs = todo

    print(f"[packs] Generating for {len(jobs)} jobs using {MODEL} ({MAX_WORKERS} workers)...", flush=True)

    done = 0
    t_start = time.time()
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = {ex.submit(process_job, j): j for j in jobs}
        for fut in concurrent.futures.as_completed(futs):
            job = futs[fut]
            try:
                content, dt, title, company, description, why, location = fut.result()
            except Exception as e:
                print(f"[O] FAIL {job.get('company','?')} / {job.get('title','?')}: {e}", flush=True)
                continue
            done += 1
            sep = content.find("===COVER_LETTER===")
            resume_md = content[:sep].strip() if sep >= 0 else content.strip()
            cover_md = content[sep + len("===COVER_LETTER==="):].strip() if sep >= 0 else ""
            # Enriched description (for the dashboard card)
            enriched = ""
            dsep = cover_md.find("===JOB_DESCRIPTION===")
            if dsep >= 0:
                enriched = cover_md[dsep + len("===JOB_DESCRIPTION==="):].strip()
                cover_md = cover_md[:dsep].strip()
            if not cover_md:
                # rough split on the second ## heading
                parts = re.split(r"\n## ", resume_md, maxsplit=1)
                if len(parts) == 2:
                    resume_md, cover_md = parts[0].strip(), "## " + parts[1].strip()

            prefix = f"{clean(company)}_{clean(title)}"
            (APP / f"{prefix}_resume.md").write_text(resume_md + "\n", encoding="utf-8")
            (APP / f"{prefix}_cover_letter.md").write_text(cover_md + "\n", encoding="utf-8")
            if enriched:
                job["enriched_description"] = enriched
            results.append({
                "company": company, "title": title, "url": job.get("url", ""),
                "location": location, "why": why, "seconds": round(dt, 1),
            })
            el = time.time() - t_start
            print(f"[OK {done}/{len(jobs)}] {company} | {title} ({dt:.0f}s, elapsed {el:.0f}s)", flush=True)

    # Write application_pack_index.json so the dashboard can also link packs.
    index = {
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "applications_submitted": False,
        "roles": [],
    }
    pack_by_url = {}
    for j in jobs:
        pack_by_url[j.get("url", "")] = j
    for r in results:
        base = f"{clean(r['company'])}_{clean(r['title'])}"
        index["roles"].append({
            "lane": "core",
            "company": r["company"],
            "title": r["title"],
            "location": r["location"],
            "application_route": r.get("url", ""),
            "application_url": r.get("url", ""),
            "resume": f"applications/{base}_resume.md",
            "cover": f"applications/{base}_cover_letter.md",
            "opening_email": "",
            "audit": {},
            "fit": "",
            "score": 0,
            "matched_skills": [],
            "missing_skills": [],
            "why": r.get("why", ""),
        })

    (ROOT / "application_pack_index.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    # Persist enriched descriptions back into the source data
    DATA.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"\n[DONE] Generated {len(results)}/{len(jobs)} packs in {time.time()-t_start:.0f}s", flush=True)
    print("Packs written to applications/*.md + application_pack_index.json", flush=True)


if __name__ == "__main__":
    main()