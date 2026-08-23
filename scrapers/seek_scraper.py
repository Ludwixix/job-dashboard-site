#!/usr/bin/env python3
"""
Seek.com.au scraper using their public API.
Falls back to web scraping if API is rate-limited.
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SEEK_API_URL = "https://chalice-search-api.cloud.seek.com.au/search"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://www.seek.com.au/",
    "Origin": "https://www.seek.com.au",
}

IT_KEYWORDS = [
    "IT support", "system administrator", "cloud engineer",
    "service desk", "desktop support", "microsoft 365",
    "azure", "intune", "infrastructure engineer",
]

MELBOURNE_WHERE = "Melbourne%2C+VIC"
MAX_PER_KEYWORD = 25


def fetch_seek_page(keyword: str, page: int = 0) -> dict:
    """Fetch a page from Seek's search API."""
    params = {
        "siteKey": "AU-Main",
        "where": MELBOURNE_WHERE,
        "keywords": keyword,
        "pageSize": 22,
        "page": page,
        "sortmode": "ListedDate",
    }
    url = f"{SEEK_API_URL}?{urllib.parse.urlencode(params)}"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"  Error: {e}", file=sys.stderr)
        return {"totalCount": 0, "jobs": []}


def normalize_seek_job(job: dict, keyword: str) -> dict:
    """Normalize a Seek job to our standard format."""
    title = job.get("title", "")
    company = job.get("advertiser", {}).get("description", job.get("advertiserDescription", ""))
    location = job.get("places", {}).get("label", "")
    if not location:
        area = job.get("area", "")
        state = job.get("state", "")
        location = f"{area}, {state}" if area else state

    salary = ""
    if job.get("salary"):
        salary = job["salary"]
    elif job.get("salaryLabel"):
        salary = job["salaryLabel"]

    return {
        "title": title,
        "company": company,
        "url": f"https://www.seek.com.au/job/{job.get('id', '')}" if job.get("id") else "",
        "location": location,
        "posted": job.get("listingDate", "")[:10],
        "source": "Seek",
        "salary": salary,
        "description": (job.get("teaser", "") or "")[:500],
        "tags": [keyword, "seek"],
        "why": f"Seek listing for {title} at {company}",
        "score": 0,
        "listing_verification": "seek_verified",
        "application_route": f"https://www.seek.com.au/job/{job.get('id', '')}" if job.get("id") else "",
        "application_route_type": "seek_direct",
        "remote": any(t.get("label", "").lower() == "remote" for t in job.get("workType", [])),
    }


def scrape_seek() -> list:
    """Scrape IT jobs from Seek."""
    all_jobs = []
    seen_ids = set()

    for keyword in IT_KEYWORDS:
        print(f"  Searching: {keyword}...")
        page = 0
        collected = 0

        while collected < MAX_PER_KEYWORD:
            data = fetch_seek_page(keyword, page)
            jobs = data.get("jobs", [])
            if not jobs:
                break

            for job in jobs:
                job_id = job.get("id", "")
                if job_id in seen_ids:
                    continue
                seen_ids.add(job_id)
                all_jobs.append(normalize_seek_job(job, keyword))
                collected += 1

                if collected >= MAX_PER_KEYWORD:
                    break

            page += 1
            time.sleep(1)  # Rate limit - Seek is aggressive

        print(f"    → {collected} jobs")
        time.sleep(2)  # Pause between keywords

    return all_jobs


def main():
    output_dir = Path(__file__).parent
    output_path = output_dir / "jobs_seek.json"

    print("Scraping Seek.com.au API...")
    jobs = scrape_seek()

    # If API returned nothing, fall back to browser scraper
    if not jobs:
        print("  API returned 0 jobs — falling back to browser scraper...")
        try:
            from seek_browser import scrape_seek_browser
            jobs = scrape_seek_browser()
            print(f"  Browser scraper returned {len(jobs)} jobs")
        except Exception as e:
            print(f"  Browser scraper also failed: {e}")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"source": "seek", "scraped_at": datetime.now(timezone.utc).isoformat(), "count": len(jobs), "jobs": jobs}, f, indent=2, ensure_ascii=False)

    print(f"\nSeek: {len(jobs)} jobs → {output_path.name}")
    return jobs


if __name__ == "__main__":
    main()
