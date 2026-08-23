#!/usr/bin/env python3
"""Unified job scraper — all sources, browser-based anti-bot bypass."""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from adzuna_scraper import scrape_adzuna
from seek_browser import scrape_seek_browser
from indeed_browser import scrape_indeed_browser
from linkedin_browser import scrape_linkedin_browser
from other_sources_scraper import scrape_jora, scrape_careerone

# Stream classification keywords
STREAM_KEYWORDS = {
    "Core IT": [
        "system administrator", "network engineer", "cloud engineer", "devops",
        "cyber security", "software engineer", "data engineer", "infrastructure",
        "platform engineer", "azure", "microsoft 365", "entra id", "intune",
        "windows server", "linux", "kubernetes", "terraform", "powershell",
        "service desk", "help desk", "desktop support", "endpoint",
        "project manager", "it support", "vmware", "database",
    ],
    "Local Bridge": [
        "retail", "warehouse", "courier", "driver", "barista", "hospitality",
        "cleaner", "gardener", "maintenance", "casual", "part time",
        "customer service", "store", "team member", "groundsperson",
        "groundskeeper", "mower", "brushcutting", "housekeeper",
    ],
    "Trade Pathways": [
        "traineeship", "apprenticeship", "technician", "cabling", "fibre",
        "data centre", "data center", "hvac", "electrician", "plumber",
        "carpentry", "air conditioning", "refrigeration", "panel beater",
        "spray painter", "conveyor", "splicing",
    ],
}


def classify_stream(job):
    """Classify a job into one of the 3 streams based on title + tags."""
    text = " ".join([
        job.get("title", ""),
        job.get("why", ""),
        " ".join(job.get("tags", [])),
    ]).lower()

    scores = {}
    for stream, keywords in STREAM_KEYWORDS.items():
        scores[stream] = sum(1 for kw in keywords if kw in text)

    best = max(scores, key=scores.get)
    if scores[best] == 0:
        # Default: if it has IT-related tags, put in Core IT
        if any(t in text for t in ["it", "tech", "engineer", "admin"]):
            return "Core IT"
        return "Local Bridge"  # Default to local/bridge
    return best


def deduplicate_jobs(all_jobs):
    """Remove duplicates across sources. Prefer LinkedIn > Adzuna > Seek > Indeed."""
    source_priority = {
        "LinkedIn": 0, "Adzuna": 1, "Seek": 2, "Indeed": 3,
        "Jora": 4, "CareerOne": 5,
    }
    all_jobs.sort(key=lambda j: source_priority.get(j.get("source", ""), 99))
    seen = {}
    deduped = []
    for job in all_jobs:
        # Dedup by company+title
        key = ((job.get("company") or "").lower().strip(), (job.get("title") or "").lower().strip())
        if key in seen:
            existing = seen[key]
            for tag in job.get("tags", []):
                if tag not in existing.get("tags", []):
                    existing.setdefault("tags", []).append(tag)
            continue
        seen[key] = job
        deduped.append(job)
    return deduped


def main():
    output_dir = Path(__file__).parent
    output_path = output_dir / "jobs_combined.json"
    all_jobs = []

    # Phase 1: Adzuna (structured API - fastest, most reliable)
    print("=" * 60)
    print("PHASE 1: Adzuna API (structured)")
    print("=" * 60)
    try:
        adzuna_jobs = scrape_adzuna()
        all_jobs.extend(adzuna_jobs)
        print(f"Adzuna: {len(adzuna_jobs)} jobs")
    except Exception as e:
        print(f"Adzuna failed: {e}")

    # Phase 2: LinkedIn (public search, no login required)
    print("\n" + "=" * 60)
    print("PHASE 2: LinkedIn (Playwright public search)")
    print("=" * 60)
    try:
        linkedin_jobs = scrape_linkedin_browser()
        all_jobs.extend(linkedin_jobs)
        print(f"LinkedIn: {len(linkedin_jobs)} jobs")
    except Exception as e:
        print(f"LinkedIn failed: {e}")

    # Phase 3: Seek (browser-based)
    print("\n" + "=" * 60)
    print("PHASE 3: Seek (Playwright browser)")
    print("=" * 60)
    try:
        seek_jobs = scrape_seek_browser()
        all_jobs.extend(seek_jobs)
        print(f"Seek: {len(seek_jobs)} jobs")
    except Exception as e:
        print(f"Seek failed: {e}")

    # Phase 4: Indeed (browser-based)
    print("\n" + "=" * 60)
    print("PHASE 4: Indeed (Playwright browser)")
    print("=" * 60)
    try:
        indeed_jobs = scrape_indeed_browser()
        all_jobs.extend(indeed_jobs)
        print(f"Indeed: {len(indeed_jobs)} jobs")
    except Exception as e:
        print(f"Indeed failed: {e}")

    # Phase 5: Other sources
    print("\n" + "=" * 60)
    print("PHASE 5: Jora + CareerOne")
    print("=" * 60)
    try:
        other_jobs = scrape_jora() + scrape_careerone()
        all_jobs.extend(other_jobs)
        print(f"Other: {len(other_jobs)} jobs")
    except Exception as e:
        print(f"Other failed: {e}")

    # Phase 6: Deduplicate
    print("\n" + "=" * 60)
    print("PHASE 6: Deduplication")
    print("=" * 60)
    before = len(all_jobs)
    deduped = deduplicate_jobs(all_jobs)
    after = len(deduped)
    print(f"Before: {before} -> After: {after} ({before - after} duplicates removed)")

    # Phase 7: Classify into streams
    print("\n" + "=" * 60)
    print("PHASE 7: Stream Classification")
    print("=" * 60)
    stream_counts = {}
    for job in deduped:
        stream = classify_stream(job)
        job["stream"] = stream
        stream_counts[stream] = stream_counts.get(stream, 0) + 1
    for stream, count in sorted(stream_counts.items()):
        print(f"  {stream}: {count} jobs")

    # Save
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "sources": {
                s: len([j for j in deduped if j.get("source") == s])
                for s in ["Adzuna", "LinkedIn", "Seek", "Indeed", "Jora", "CareerOne"]
            },
            "streams": stream_counts,
            "total": len(deduped),
            "jobs": deduped,
        }, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 60}")
    print(f"COMPLETE: {len(deduped)} unique jobs -> {output_path.name}")
    print(f"{'=' * 60}")
    return deduped


if __name__ == "__main__":
    main()
