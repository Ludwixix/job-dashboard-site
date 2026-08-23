#!/usr/bin/env python3
"""Deduplicate jobs across all sections in the job JSON.

Removes exact URL duplicates within each section and fuzzy duplicates
(same company + same title) within each section.
"""
import json
import sys
from pathlib import Path


def deduplicate_exact(jobs: list) -> tuple[list, int]:
    """Remove exact URL duplicates. Keeps first occurrence."""
    seen = set()
    deduped = []
    removed = 0
    for job in jobs:
        url = job.get("url", "")
        if url and url in seen:
            removed += 1
            continue
        if url:
            seen.add(url)
        deduped.append(job)
    return deduped, removed


def deduplicate_fuzzy(jobs: list) -> tuple[list, int]:
    """Remove fuzzy duplicates: same company + same title.
    Keeps the job with the higher score."""
    seen = {}
    deduped = []
    removed = 0
    for job in jobs:
        key = (
            (job.get("company") or "").lower().strip(),
            (job.get("title") or "").lower().strip(),
        )
        if key in seen:
            existing_idx = seen[key]
            if (job.get("score") or 0) > (deduped[existing_idx].get("score") or 0):
                deduped[existing_idx] = job
            removed += 1
            continue
        seen[key] = len(deduped)
        deduped.append(job)
    return deduped, removed


def main():
    input_path = Path(__file__).parent / "jobs_nonlinkedin_2026-08-08.json"
    output_path = Path(__file__).parent / "jobs_nonlinkedin_2026-08-08_clean.json"

    if not input_path.exists():
        print(f"Error: {input_path} not found")
        sys.exit(1)

    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)

    total_removed = 0

    # Process each section independently
    # Core jobs
    core = data.get("jobs", [])
    core, r = deduplicate_exact(core)
    total_removed += r
    core, r = deduplicate_fuzzy(core)
    total_removed += r
    data["jobs"] = core
    print(f"core: {len(core)} jobs ({r} fuzzy + exact removed)")

    # Each section independently
    for section_name in list(data.get("sections", {}).keys()):
        section = data["sections"][section_name]
        before = len(section)
        section, r1 = deduplicate_exact(section)
        section, r2 = deduplicate_fuzzy(section)
        data["sections"][section_name] = section
        total_removed += r1 + r2
        print(f"{section_name}: {len(section)} jobs ({r1 + r2} removed)")

    # Cross-section dedup: remove from sections if already in core
    core_urls = set(j.get("url") for j in data["jobs"])
    for section_name in list(data["sections"].keys()):
        section = data["sections"][section_name]
        before = len(section)
        data["sections"][section_name] = [j for j in section if j.get("url") not in core_urls]
        cross_removed = before - len(data["sections"][section_name])
        if cross_removed:
            total_removed += cross_removed
            print(f"{section_name}: -{cross_removed} cross-section dedup")

    print(f"\nTotal duplicates removed: {total_removed}")
    print("\nFinal counts:")
    print(f"  core: {len(data['jobs'])}")
    for name, jobs in data.get("sections", {}).items():
        print(f"  {name}: {len(jobs)}")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n→ {output_path.name}")


if __name__ == "__main__":
    main()
