#!/usr/bin/env python3
"""
Adzuna API scraper for IT jobs in Melbourne.
Fetches jobs from Adzuna's structured API with proper rate limiting.
"""
import json
import sys
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

APP_ID = "cc30c73e"
APP_KEY = "567d2e59986920554a8b4a08359d35fe"
BASE_URL = "https://api.adzuna.com/v1/api/jobs/au/search"

# IT search terms mapped to Adzuna category codes
IT_SEARCHES = [
    # Core IT
    ("IT support", "it_support"),
    ("system administrator", "sysadmin"),
    ("network engineer", "network"),
    ("cloud engineer", "cloud"),
    ("devops engineer", "devops"),
    ("cyber security", "security"),
    ("software engineer", "software"),
    ("data engineer", "data"),
    ("project manager IT", "pm_it"),
    ("service desk", "service_desk"),
    ("help desk", "helpdesk"),
    ("desktop support", "desktop_support"),
    # M365 / Identity
    ("microsoft 365", "m365"),
    ("azure admin", "azure"),
    ("entra id", "entra"),
    ("intune", "intune"),
    # Infrastructure
    ("windows server", "windows_server"),
    ("linux admin", "linux"),
    ("vmware", "vmware"),
    ("kubernetes", "k8s"),
    ("terraform", "terraform"),
]

# Location focus
LOCATION = "Melbourne, Victoria"
MAX_PER_SEARCH = 50  # Adzuna free tier limit
RESULTS_PER_PAGE = 50


def fetch_page(page: int, what: str) -> dict:
    """Fetch a single page of results from Adzuna."""
    params = urllib.parse.urlencode({
        "app_id": APP_ID,
        "app_key": APP_KEY,
        "results_per_page": RESULTS_PER_PAGE,
        "what": what,
        "where": LOCATION,
        "content-type": "application/json",
        "sort_by": "date",
        "max_days_old": 14,  # Only last 2 weeks
    })
    url = f"{BASE_URL}/{page}?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "JobDashboard/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"  Error fetching page {page} for '{what}': {e}", file=sys.stderr)
        return {"count": 0, "results": []}


def normalize_job(job: dict, search_tag: str) -> dict:
    """Normalize an Adzuna job to our standard format."""
    title = job.get("title", "")
    company = job.get("company", {}).get("display_name", "")
    location_parts = job.get("location", {}).get("area", [])
    location = ", ".join(location_parts[-2:]) if len(location_parts) >= 2 else job.get("location", {}).get("display_name", "")

    # Parse salary
    salary_min = job.get("salary_min")
    salary_max = job.get("salary_max")
    salary = ""
    if salary_min and salary_max:
        salary = f"${int(salary_min):,} – ${int(salary_max):,}"
    elif salary_min:
        salary = f"From ${int(salary_min):,}"
    elif salary_max:
        salary = f"Up to ${int(salary_max):,}"

    # Parse description (strip HTML tags)
    desc = job.get("description", "")
    import re
    desc = re.sub(r"<[^>]+>", " ", desc).strip()
    desc = re.sub(r"\s+", " ", desc)

    return {
        "title": title,
        "company": company,
        "url": job.get("redirect_url", ""),
        "location": location,
        "posted": (job.get("created", "") or "")[:10],
        "source": "Adzuna",
        "salary": salary,
        "description": desc[:500],
        "tags": [search_tag, "adzuna"],
        "why": f"Adzuna listing for {title} at {company}",
        "score": 0,  # Will be scored later
        "listing_verification": "api_verified",
        "application_route": job.get("redirect_url", ""),
        "application_route_type": "adzuna_api",
        "remote": "remote" in title.lower() or "remote" in desc.lower()[:200],
    }


def scrape_adzuna() -> list:
    """Scrape all IT jobs from Adzuna."""
    all_jobs = []
    seen_urls = set()

    for what, tag in IT_SEARCHES:
        print(f"  Searching: {what} ({tag})...")
        page = 1
        collected = 0

        while collected < MAX_PER_SEARCH:
            data = fetch_page(page, what)
            results = data.get("results", [])
            if not results:
                break

            for job in results:
                url = job.get("redirect_url", "")
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                all_jobs.append(normalize_job(job, tag))
                collected += 1

                if collected >= MAX_PER_SEARCH:
                    break

            page += 1
            time.sleep(0.5)  # Rate limit

        print(f"    → {collected} jobs")
        time.sleep(1)  # Pause between searches

    return all_jobs


def main():
    output_dir = Path(__file__).parent
    output_path = output_dir / "jobs_adzuna.json"

    print("Scraping Adzuna API...")
    jobs = scrape_adzuna()

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"source": "adzuna", "scraped_at": datetime.now(timezone.utc).isoformat(), "count": len(jobs), "jobs": jobs}, f, indent=2, ensure_ascii=False)

    print(f"\nAdzuna: {len(jobs)} jobs → {output_path.name}")
    return jobs


if __name__ == "__main__":
    main()
