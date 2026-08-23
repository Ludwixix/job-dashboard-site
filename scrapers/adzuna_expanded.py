#!/usr/bin/env python3
"""
Additional job API sources that don't have aggressive anti-bot.
Uses Adzuna (already working) plus other structured APIs.
"""
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def scrape_adzuna_melbourne():
    """Scrape Adzuna with expanded searches for better coverage."""
    APP_ID = "cc30c73e"
    APP_KEY = "567d2e59986920554a8b4a08359d35fe"
    BASE_URL = "https://api.adzuna.com/v1/api/jobs/au/search"

    # Expanded search terms
    searches = [
        # IT Support & Service Desk
        "IT support", "help desk", "service desk", "desktop support",
        "technical support", "IT helpdesk", "L1 support", "L2 support",
        # Systems & Infrastructure
        "system administrator", "sysadmin", "windows administrator",
        "linux administrator", "network administrator", "network engineer",
        "infrastructure engineer", "infrastructure analyst",
        # Cloud & DevOps
        "cloud engineer", "cloud architect", "devops engineer", "SRE",
        "platform engineer", "azure engineer", "aws engineer",
        "kubernetes", "terraform", "docker",
        # Security
        "cyber security", "security analyst", "SOC analyst",
        "penetration tester", "security engineer", "compliance analyst",
        # M365 & Identity
        "microsoft 365", "M365 admin", "entra id", "azure ad",
        "intune", "endpoint manager", "EUC engineer",
        # Software & Data
        "software engineer", "developer", "data engineer",
        "data analyst", "python developer", "full stack",
        # Management
        "IT project manager", "IT manager", "IT director",
        "scrum master", "agile coach", "business analyst IT",
        # Specialized
        "Citrix", "VMware engineer", "telecom engineer",
        "NBN", "data centre", "IT procurement",
    ]

    all_jobs = []
    seen_urls = set()

    for what in searches:
        params = urllib.parse.urlencode({
            "app_id": APP_ID,
            "app_key": APP_KEY,
            "results_per_page": 50,
            "what": what,
            "where": "Melbourne, Victoria",
            "content-type": "application/json",
            "sort_by": "date",
            "max_days_old": 14,
        })
        url = f"{BASE_URL}/1?{params}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "JobDashboard/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())

            for job in data.get("results", []):
                job_url = job.get("redirect_url", "")
                if job_url in seen_urls:
                    continue
                seen_urls.add(job_url)

                title = job.get("title", "")
                company = job.get("company", {}).get("display_name", "")
                location_parts = job.get("location", {}).get("area", [])
                location = ", ".join(location_parts[-2:]) if len(location_parts) >= 2 else ""

                desc = job.get("description", "")
                import re
                desc = re.sub(r"<[^>]+>", " ", desc).strip()
                desc = re.sub(r"\s+", " ", desc)

                salary_min = job.get("salary_min")
                salary_max = job.get("salary_max")
                salary = ""
                if salary_min and salary_max:
                    salary = f"${int(salary_min):,} – ${int(salary_max):,}"

                all_jobs.append({
                    "title": title,
                    "company": company,
                    "url": job_url,
                    "location": location,
                    "posted": (job.get("created", "") or "")[:10],
                    "source": "Adzuna",
                    "salary": salary,
                    "description": desc[:500],
                    "tags": [what.split()[0].lower(), "adzuna"],
                    "why": f"Adzuna listing for {title} at {company}",
                    "score": 0,
                    "listing_verification": "api_verified",
                    "application_route": job_url,
                    "application_route_type": "adzuna_api",
                    "remote": "remote" in title.lower() or "remote" in desc.lower()[:200],
                })

            time.sleep(0.3)
        except Exception:
            pass

    return all_jobs


def main():
    output_dir = Path(__file__).parent
    output_path = output_dir / "jobs_adzuna_expanded.json"

    print("Scraping Adzuna (expanded searches)...")
    jobs = scrape_adzuna_melbourne()

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "source": "adzuna_expanded",
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "count": len(jobs),
            "jobs": jobs,
        }, f, indent=2, ensure_ascii=False)

    print(f"\nAdzuna expanded: {len(jobs)} jobs -> {output_path.name}")
    return jobs


if __name__ == "__main__":
    main()
