#!/usr/bin/env python3
"""Indeed.com.au scraper using HTML scraping."""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-AU,en;q=0.9",
}

IT_KEYWORDS = [
    "IT support", "system administrator", "network engineer",
    "cloud engineer", "devops", "cyber security", "software engineer",
    "data engineer", "service desk", "help desk", "desktop support",
    "microsoft 365", "azure", "intune", "windows server", "linux admin",
    "infrastructure engineer", "endpoint engineer",
]

MAX_PER_KEYWORD = 20


def fetch_indeed_page(keyword, start=0):
    """Fetch Indeed search results HTML."""
    params = urllib.parse.urlencode({
        "q": keyword,
        "l": "Melbourne, VIC",
        "sort": "date",
        "fromage": 14,
        "start": start,
    })
    url = f"https://au.indeed.com/jobs?{params}"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  Error fetching Indeed: {e}", file=sys.stderr)
        return ""


def parse_indeed_jobs(html, keyword):
    """Parse job listings from Indeed HTML."""
    jobs = []
    job_pattern = re.compile(
        r'<a[^>]*href="(/rc/clk[^"]*|/viewjob\?[^"]*)"[^>]*>.*?'
        r'<h2[^>]*>(.*?)</h2>.*?'
        r'<span[^>]*data-testid="company-name"[^>]*>(.*?)</span>.*?'
        r'<div[^>]*data-testid="text-location"[^>]*>(.*?)</div>',
        re.DOTALL
    )
    simple_pattern = re.compile(
        r'<h2[^>]*class="jobTitle[^"]*"[^>]*>\s*<a[^>]*href="(/rc/clk[^"]*|/viewjob\?[^"]*)"[^>]*>(.*?)</a>.*?'
        r'<span[^>]*data-testid="company-name"[^>]*>(.*?)</span>',
        re.DOTALL
    )

    for match in job_pattern.finditer(html):
        url_path, title, company, location = match.groups()
        title = re.sub(r'<[^>]+>', '', title).strip()
        company = re.sub(r'<[^>]+>', '', company).strip()
        location = re.sub(r'<[^>]+>', '', location).strip()
        full_url = f"https://au.indeed.com{url_path}" if url_path.startswith("/") else url_path
        jobs.append({
            "title": title, "company": company, "url": full_url,
            "location": location, "posted": "", "source": "Indeed",
            "salary": "", "description": "",
            "tags": [keyword, "indeed"],
            "why": f"Indeed listing for {title} at {company}",
            "score": 0, "listing_verification": "web_scraped",
            "application_route": full_url, "application_route_type": "indeed_direct",
            "remote": "remote" in title.lower(),
        })

    if not jobs:
        for match in simple_pattern.finditer(html):
            url_path, title, company = match.groups()
            title = re.sub(r'<[^>]+>', '', title).strip()
            company = re.sub(r'<[^>]+>', '', company).strip()
            full_url = f"https://au.indeed.com{url_path}" if url_path.startswith("/") else url_path
            jobs.append({
                "title": title, "company": company, "url": full_url,
                "location": "Melbourne, VIC", "posted": "", "source": "Indeed",
                "salary": "", "description": "",
                "tags": [keyword, "indeed"],
                "why": f"Indeed listing for {title} at {company}",
                "score": 0, "listing_verification": "web_scraped",
                "application_route": full_url, "application_route_type": "indeed_direct",
                "remote": "remote" in title.lower(),
            })
    return jobs


def scrape_indeed():
    """Scrape IT jobs from Indeed."""
    all_jobs = []
    seen_urls = set()
    for keyword in IT_KEYWORDS:
        print(f"  Searching: {keyword}...")
        start = 0
        collected = 0
        while collected < MAX_PER_KEYWORD:
            html = fetch_indeed_page(keyword, start)
            if not html:
                break
            jobs = parse_indeed_jobs(html, keyword)
            if not jobs:
                break
            for job in jobs:
                if job["url"] in seen_urls:
                    continue
                seen_urls.add(job["url"])
                all_jobs.append(job)
                collected += 1
                if collected >= MAX_PER_KEYWORD:
                    break
            start += 10
            time.sleep(2)
        print(f"    -> {collected} jobs")
        time.sleep(3)
    return all_jobs


def main():
    output_dir = Path(__file__).parent
    output_path = output_dir / "jobs_indeed.json"
    print("Scraping Indeed.com.au...")
    jobs = scrape_indeed()
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"source": "indeed", "scraped_at": datetime.now(timezone.utc).isoformat(), "count": len(jobs), "jobs": jobs}, f, indent=2, ensure_ascii=False)
    print(f"\nIndeed: {len(jobs)} jobs -> {output_path.name}")
    return jobs


if __name__ == "__main__":
    main()
