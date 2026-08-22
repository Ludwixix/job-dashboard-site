#!/usr/bin/env python3
"""Unified job scraper with browser-based anti-bot bypass."""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from adzuna_scraper import scrape_adzuna
from seek_browser import scrape_seek_browser
from indeed_browser import scrape_indeed_browser
from other_sources_scraper import scrape_jora, scrape_careerone


def deduplicate_jobs(all_jobs):
    """Remove duplicates across sources. Prefer Adzuna > Seek > Indeed."""
    source_priority = {"Adzuna": 0, "Seek": 1, "Indeed": 2, "Jora": 3, "CareerOne": 4}
    all_jobs.sort(key=lambda j: source_priority.get(j.get("source", ""), 99))
    seen = {}
    deduped = []
    for job in all_jobs:
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

    # Phase 1: Adzuna (structured API - fastest)
    print("=" * 60)
    print("PHASE 1: Adzuna API (structured)")
    print("=" * 60)
    try:
        adzuna_jobs = scrape_adzuna()
        all_jobs.extend(adzuna_jobs)
        print(f"Adzuna: {len(adzuna_jobs)} jobs")
    except Exception as e:
        print(f"Adzuna failed: {e}")

    # Phase 2: Seek (browser-based)
    print("\n" + "=" * 60)
    print("PHASE 2: Seek (Playwright browser)")
    print("=" * 60)
    try:
        seek_jobs = scrape_seek_browser()
        all_jobs.extend(seek_jobs)
        print(f"Seek: {len(seek_jobs)} jobs")
    except Exception as e:
        print(f"Seek failed: {e}")

    # Phase 3: Indeed (browser-based)
    print("\n" + "=" * 60)
    print("PHASE 3: Indeed (Playwright browser)")
    print("=" * 60)
    try:
        indeed_jobs = scrape_indeed_browser()
        all_jobs.extend(indeed_jobs)
        print(f"Indeed: {len(indeed_jobs)} jobs")
    except Exception as e:
        print(f"Indeed failed: {e}")

    # Phase 4: Other sources
    print("\n" + "=" * 60)
    print("PHASE 4: Jora + CareerOne")
    print("=" * 60)
    try:
        other_jobs = scrape_jora() + scrape_careerone()
        all_jobs.extend(other_jobs)
        print(f"Other: {len(other_jobs)} jobs")
    except Exception as e:
        print(f"Other failed: {e}")

    # Phase 5: Deduplicate
    print("\n" + "=" * 60)
    print("PHASE 5: Deduplication")
    print("=" * 60)
    before = len(all_jobs)
    deduped = deduplicate_jobs(all_jobs)
    after = len(deduped)
    print(f"Before: {before} -> After: {after} ({before - after} duplicates removed)")

    # Save
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "sources": {s: len([j for j in deduped if j.get("source") == s]) for s in ["Adzuna", "Seek", "Indeed", "Jora", "CareerOne"]},
            "total": len(deduped),
            "jobs": deduped,
        }, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 60}")
    print(f"COMPLETE: {len(deduped)} unique jobs -> {output_path.name}")
    print(f"{'=' * 60}")
    return deduped


if __name__ == "__main__":
    main()
