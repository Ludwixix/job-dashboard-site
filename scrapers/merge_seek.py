#!/usr/bin/env python3
"""
Quick integration: merge Seek robust scraper output into jobs_combined.json.
Run seek_robust.py first, then this script.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRAPERS_DIR = Path(__file__).parent
SEEK_PATH = SCRAPERS_DIR / "jobs_seek_robust.json"
COMBINED_PATH = SCRAPERS_DIR / "jobs_combined.json"


def merge_seek():
    # Load Seek data
    if not SEEK_PATH.exists():
        print(f"No Seek data at {SEEK_PATH}")
        print("Run: python3 seek_robust.py --strategy playwright")
        sys.exit(1)

    seek_data = json.loads(SEEK_PATH.read_text(encoding="utf-8"))
    seek_jobs = seek_data.get("jobs", [])
    print(f"Seek jobs: {len(seek_jobs)}")

    if not seek_jobs:
        print("No Seek jobs to merge")
        return

    # Load existing combined data
    if COMBINED_PATH.exists():
        combined = json.loads(COMBINED_PATH.read_text(encoding="utf-8"))
    else:
        combined = {"jobs": [], "sources": {}}

    existing_jobs = combined.get("jobs", [])
    print(f"Existing combined jobs: {len(existing_jobs)}")

    # Build dedup keys from existing
    seen = set()
    for j in existing_jobs:
        key = (
            (j.get("company") or "").lower().strip(),
            (j.get("title") or "").lower().strip(),
        )
        seen.add(key)
        # Also dedup by URL
        url = (j.get("url") or j.get("application_route") or "").rstrip("/")
        if url:
            seen.add(url)

    # Merge Seek jobs
    added = 0
    for job in seek_jobs:
        # Check by title+company
        key = (
            (job.get("company") or "").lower().strip(),
            (job.get("title") or "").lower().strip(),
        )
        # Check by URL
        url = (job.get("url") or job.get("application_route") or "").rstrip("/")

        if key in seen or (url and url in seen):
            continue

        existing_jobs.append(job)
        seen.add(key)
        if url:
            seen.add(url)
        added += 1

    print(f"Added {added} new Seek jobs")

    # Update source counts
    sources = combined.get("sources", {})
    sources["Seek"] = sources.get("Seek", 0) + added
    combined["sources"] = sources
    combined["jobs"] = existing_jobs
    combined["total"] = len(existing_jobs)
    combined["updated"] = datetime.now(timezone.utc).isoformat()
    combined["scraped_at"] = datetime.now(timezone.utc).isoformat()

    # Write back
    COMBINED_PATH.write_text(
        json.dumps(combined, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Combined: {len(existing_jobs)} total jobs → {COMBINED_PATH.name}")

    # Source breakdown
    src_counts = {}
    for j in existing_jobs:
        s = j.get("source", "Unknown")
        src_counts[s] = src_counts.get(s, 0) + 1
    print("Sources:")
    for s, c in sorted(src_counts.items(), key=lambda x: -x[1]):
        print(f"  {s}: {c}")


if __name__ == "__main__":
    merge_seek()
