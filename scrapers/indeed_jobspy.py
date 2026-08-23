#!/usr/bin/env python3
"""
Indeed scraper using python-jobspy.
Bypasses Cloudflare via JobSpy's built-in TLS client.
"""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    from jobspy import scrape_jobs
except ImportError:
    print("Install python-jobspy: pip install python-jobspy")
    sys.exit(1)

IT_KEYWORDS = [
    ("IT support", "Melbourne, VIC"),
    ("system administrator", "Melbourne, VIC"),
    ("network engineer", "Melbourne, VIC"),
    ("cloud engineer", "Melbourne, VIC"),
    ("devops engineer", "Melbourne, VIC"),
    ("cyber security", "Melbourne, VIC"),
    ("service desk", "Melbourne, VIC"),
    ("help desk", "Melbourne, VIC"),
    ("desktop support", "Melbourne, VIC"),
    ("infrastructure engineer", "Melbourne, VIC"),
    ("platform engineer", "Melbourne, VIC"),
    ("microsoft 365", "Melbourne, VIC"),
    ("azure", "Melbourne, VIC"),
    ("data engineer", "Melbourne, VIC"),
]

BRIDGE_KEYWORDS = [
    ("casual work", "Melbourne, VIC"),
    ("warehouse", "Melbourne, VIC"),
    ("hospitality", "Melbourne, VIC"),
    ("retail", "Melbourne, VIC"),
    ("courier", "Melbourne, VIC"),
]

TRADE_KEYWORDS = [
    ("traineeship", "Melbourne, VIC"),
    ("apprenticeship", "Melbourne, VIC"),
    ("data centre technician", "Melbourne, VIC"),
    ("hvac", "Melbourne, VIC"),
    ("cabling", "Melbourne, VIC"),
    ("electrician", "Melbourne, VIC"),
]


def scrape_indeed():
    """Scrape Indeed via JobSpy."""
    all_jobs = []
    seen_urls = set()

    all_keywords = [
        ("core_it", IT_KEYWORDS),
        ("bridge", BRIDGE_KEYWORDS),
        ("traineeship", TRADE_KEYWORDS),
    ]

    for stream, keywords in all_keywords:
        print(f"\n  Stream: {stream}")
        for search_term, location in keywords:
            print(f"    Searching: {search_term}...")
            try:
                results = scrape_jobs(
                    site_name=["indeed"],
                    search_term=search_term,
                    location=location,
                    country_indeed="australia",
                    results_wanted=20,
                    hours_old=336,  # 14 days
                )

                if results is None or len(results) == 0:
                    print(f"      -> 0 results")
                    continue

                for _, row in results.iterrows():
                    url = row.get("job_url", "")
                    if not url or url in seen_urls:
                        continue
                    seen_urls.add(url)

                    # Determine stream from keyword group
                    stream_label = "Core IT"
                    if stream == "bridge":
                        stream_label = "Local Bridge"
                    elif stream == "traineeship":
                        stream_label = "Trade Pathways"

                    salary = ""
                    if row.get("min_amount") and row.get("max_amount"):
                        salary = f"${row['min_amount']}-${row['max_amount']} {row.get('interval', 'per year')}"
                    elif row.get("min_amount"):
                        salary = f"${row['min_amount']} {row.get('interval', 'per year')}"

                    all_jobs.append({
                        "title": row.get("title", ""),
                        "company": row.get("company", ""),
                        "url": url,
                        "location": row.get("location", "Melbourne, VIC"),
                        "posted": str(row.get("date_posted", ""))[:10],
                        "source": "Indeed",
                        "salary": salary,
                        "description": str(row.get("description", ""))[:500] if row.get("description") else "",
                        "tags": [search_term.lower(), "indeed", stream_label.lower().replace(" ", "_")],
                        "why": f"Indeed listing for {row.get('title', '')} at {row.get('company', '')}",
                        "score": 0,
                        "listing_verification": "indeed_jobspy",
                        "application_route": url,
                        "application_route_type": "indeed_direct",
                        "remote": bool(row.get("is_remote")),
                        "stream": stream_label,
                    })

                print(f"      -> {len(results)} results")
                time.sleep(3)  # Rate limit

            except Exception as e:
                print(f"      Error: {e}")
                time.sleep(5)

    return all_jobs


def main():
    output_dir = Path(__file__).parent
    output_path = output_dir / "jobs_indeed_jobspy.json"

    print("Scraping Indeed via JobSpy...")
    jobs = scrape_indeed()

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "source": "indeed_jobspy",
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "count": len(jobs),
            "jobs": jobs,
        }, f, indent=2, ensure_ascii=False)

    print(f"\nIndeed (JobSpy): {len(jobs)} jobs -> {output_path.name}")
    return jobs


if __name__ == "__main__":
    main()
