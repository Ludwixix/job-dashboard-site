#!/usr/bin/env python3
"""Final unified scraper - combines all working sources."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from adzuna_expanded import scrape_adzuna_melbourne
from adzuna_scraper import scrape_adzuna


def deduplicate_jobs(all_jobs):
    """Remove duplicates by URL and fuzzy company+title."""
    # Dedup by URL
    seen_urls = {}
    for job in all_jobs:
        url = job.get("url", "")
        if url and url not in seen_urls:
            seen_urls[url] = job
        elif url:
            # Merge tags
            existing = seen_urls[url]
            for tag in job.get("tags", []):
                if tag not in existing.get("tags", []):
                    existing.setdefault("tags", []).append(tag)

    # Dedup by company+title
    by_url = list(seen_urls.values())
    seen_key = {}
    deduped = []
    for job in by_url:
        key = ((job.get("company") or "").lower().strip(), (job.get("title") or "").lower().strip())
        if key in seen_key:
            existing = seen_key[key]
            for tag in job.get("tags", []):
                if tag not in existing.get("tags", []):
                    existing.setdefault("tags", []).append(tag)
            continue
        seen_key[key] = job
        deduped.append(job)

    return deduped


def main():
    output_dir = Path(__file__).parent
    output_path = output_dir / "jobs_combined.json"
    all_jobs = []

    # Phase 1: Adzuna basic
    print("=" * 60)
    print("PHASE 1: Adzuna API (basic)")
    print("=" * 60)
    try:
        jobs = scrape_adzuna()
        all_jobs.extend(jobs)
        print(f"Adzuna basic: {len(jobs)} jobs")
    except Exception as e:
        print(f"Failed: {e}")

    # Phase 2: Adzuna expanded
    print("\n" + "=" * 60)
    print("PHASE 2: Adzuna API (expanded)")
    print("=" * 60)
    try:
        jobs = scrape_adzuna_melbourne()
        all_jobs.extend(jobs)
        print(f"Adzuna expanded: {len(jobs)} jobs")
    except Exception as e:
        print(f"Failed: {e}")

    # Phase 3: Deduplicate
    print("\n" + "=" * 60)
    print("PHASE 3: Deduplication")
    print("=" * 60)
    before = len(all_jobs)
    deduped = deduplicate_jobs(all_jobs)
    after = len(deduped)
    print(f"Before: {before} -> After: {after} ({before - after} duplicates removed)")

    # Save
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "sources": {"Adzuna": len(deduped)},
            "total": len(deduped),
            "jobs": deduped,
        }, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 60}")
    print(f"COMPLETE: {len(deduped)} unique jobs -> {output_path.name}")
    print(f"{'=' * 60}")
    return deduped


if __name__ == "__main__":
    main()
