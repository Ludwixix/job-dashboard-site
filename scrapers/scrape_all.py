#!/usr/bin/env python3
"""Unified job scraper — all sources, 14-day window, top 20 per stream."""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))
from adzuna_scraper import scrape_adzuna
from indeed_jobspy import scrape_indeed
from linkedin_browser import scrape_linkedin_browser
from seek_browser import scrape_seek_browser

from stream_classifier import classify_all_jobs


def is_within_14_days(job):
    """Check if a job was posted within the last 14 days."""
    posted = job.get("posted", "")
    if not posted:
        return True  # If no date, include it (can't filter)

    try:
        # Try various date formats
        for fmt in ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ",
                     "%d/%m/%Y", "%d %b %Y", "%B %d, %Y"]:
            try:
                job_date = datetime.strptime(posted[:10], fmt[:len(posted[:10])])
                cutoff = datetime.now() - timedelta(days=14)
                return job_date >= cutoff
            except ValueError:
                continue

        # Try ISO format
        job_date = datetime.fromisoformat(posted.replace("Z", "+00:00"))
        cutoff = datetime.now(timezone.utc) - timedelta(days=14)
        return job_date >= cutoff
    except:
        return True  # If we can't parse, include it


def deduplicate_jobs(all_jobs):
    """Remove duplicates across sources. Prefer LinkedIn > Adzuna > Seek > Indeed."""
    source_priority = {
        "LinkedIn": 0, "Adzuna": 1, "Seek": 2, "Indeed": 3,
    }
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
    repo_dir = output_dir.parent
    output_path = repo_dir / "index.html"
    data_path = output_dir / "jobs_combined.json"
    all_jobs = []

    # Phase 1: Adzuna (structured API - fastest)
    print("=" * 60)
    print("PHASE 1: Adzuna API")
    print("=" * 60)
    try:
        adzuna_jobs = scrape_adzuna()
        all_jobs.extend(adzuna_jobs)
        print(f"Adzuna: {len(adzuna_jobs)} jobs")
    except Exception as e:
        print(f"Adzuna failed: {e}")

    # Phase 2: LinkedIn (public search)
    print("\n" + "=" * 60)
    print("PHASE 2: LinkedIn (Playwright)")
    print("=" * 60)
    try:
        linkedin_jobs = scrape_linkedin_browser()
        all_jobs.extend(linkedin_jobs)
        print(f"LinkedIn: {len(linkedin_jobs)} jobs")
    except Exception as e:
        print(f"LinkedIn failed: {e}")

    # Phase 3: Seek (browser-based)
    print("\n" + "=" * 60)
    print("PHASE 3: Seek (Playwright)")
    print("=" * 60)
    try:
        seek_jobs = scrape_seek_browser()
        all_jobs.extend(seek_jobs)
        print(f"Seek: {len(seek_jobs)} jobs")
    except Exception as e:
        print(f"Seek failed: {e}")

    # Phase 4: Indeed (via JobSpy)
    print("\n" + "=" * 60)
    print("PHASE 4: Indeed (JobSpy)")
    print("=" * 60)
    try:
        indeed_jobs = scrape_indeed()
        all_jobs.extend(indeed_jobs)
        print(f"Indeed: {len(indeed_jobs)} jobs")
    except Exception as e:
        print(f"Indeed failed: {e}")

    # Phase 5: Deduplicate
    print("\n" + "=" * 60)
    print("PHASE 5: Deduplication")
    print("=" * 60)
    before = len(all_jobs)
    deduped = deduplicate_jobs(all_jobs)
    after = len(deduped)
    print(f"Before: {before} -> After: {after} ({before - after} duplicates removed)")

    # Phase 6: Filter to 14 days
    print("\n" + "=" * 60)
    print("PHASE 6: 14-Day Filter")
    print("=" * 60)
    before_14 = len(deduped)
    recent = [j for j in deduped if is_within_14_days(j)]
    print(f"Before: {before_14} -> After: {len(recent)} (within 14 days)")

    # Phase 7: Classify into streams
    print("\n" + "=" * 60)
    print("PHASE 7: Stream Classification")
    print("=" * 60)
    stream_map = classify_all_jobs(recent)
    # Map stream IDs to display names
    stream_name_map = {"core-it": "Core IT", "bridge": "Local Bridge", "traineeship": "Trade Pathways"}
    stream_counts = {}
    for job in recent:
        # Find which stream this job belongs to
        for stream_id, stream_jobs in stream_map.items():
            if job in stream_jobs:
                job["stream"] = stream_name_map.get(stream_id, stream_id)
                break
        stream = job.get("stream", "Core IT")
        stream_counts[stream] = stream_counts.get(stream, 0) + 1
    for stream, count in sorted(stream_counts.items()):
        print(f"  {stream}: {count} jobs")

    # Phase 8: Top 20 per stream (by score, then recency)
    print("\n" + "=" * 60)
    print("PHASE 8: Top 20 Per Stream")
    print("=" * 60)
    top_jobs = []
    for stream in ["Core IT", "Local Bridge", "Trade Pathways"]:
        stream_jobs = [j for j in recent if j.get("stream") == stream]
        # Sort by score (desc), then by posted date (most recent first)
        stream_jobs.sort(key=lambda j: (
            -j.get("score", 0),
            j.get("posted", "9999"),  # Latest dates sort last, so reverse
        ), reverse=True)
        top = stream_jobs[:20]
        top_jobs.extend(top)
        print(f"  {stream}: {len(top)} jobs selected")

    # Save combined data
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump({
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "sources": {
                s: len([j for j in top_jobs if j.get("source") == s])
                for s in ["Adzuna", "LinkedIn", "Seek", "Indeed"]
            },
            "streams": {s: len([j for j in top_jobs if j.get("stream") == s])
                        for s in ["Core IT", "Local Bridge", "Trade Pathways"]},
            "total": len(top_jobs),
            "jobs": top_jobs,
        }, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 60}")
    print(f"COMPLETE: {len(top_jobs)} jobs -> {data_path.name}")
    print(f"{'=' * 60}")

    # Build dashboard
    print("\nBuilding dashboard...")
    sys.path.insert(0, str(repo_dir))
    from build_categorized_dashboard import build_dashboard
    build_dashboard(str(data_path), str(output_path))
    print(f"Dashboard -> {output_path.name}")

    return top_jobs


if __name__ == "__main__":
    main()
