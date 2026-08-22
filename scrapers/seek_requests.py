#!/usr/bin/env python3
"""
Seek scraper using requests with browser fingerprinting.
Uses proper headers, cookies, and session handling to bypass basic anti-bot.
"""
import json
import re
import sys
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

# Try to use requests if available, fallback to urllib
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-AU,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
    "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
}

SEEK_API_URL = "https://chalice-search-api.cloud.seek.com.au/search"

IT_KEYWORDS = [
    "IT support", "system administrator", "network engineer",
    "cloud engineer", "devops", "cyber security", "software engineer",
    "data engineer", "service desk", "help desk", "desktop support",
    "microsoft 365", "azure", "intune", "windows server", "linux admin",
    "kubernetes", "terraform", "infrastructure engineer",
]

MAX_PER_KEYWORD = 25


def fetch_seek_api(keyword, page=0):
    """Try Seek's search API directly."""
    params = {
        "siteKey": "AU-Main",
        "where": "Melbourne%2C+VIC",
        "keywords": keyword,
        "pageSize": 22,
        "page": page,
        "sortmode": "ListedDate",
    }
    url = f"{SEEK_API_URL}?{urllib.parse.urlencode(params)}"

    try:
        if HAS_REQUESTS:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                return resp.json()
        else:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
    except Exception as e:
        pass
    return None


def fetch_seek_page(keyword, start=0):
    """Fetch Seek search page HTML."""
    params = urllib.parse.urlencode({
        "keywords": keyword,
        "where": "Melbourne VIC",
        "sortmode": "ListedDate",
        "daterange": "14",  # Last 14 days
    })
    url = f"https://www.seek.com.au/{keyword.replace(' ', '-')}-jobs/in-All-Melbourne-VIC?{params}"

    try:
        if HAS_REQUESTS:
            session = requests.Session()
            # First visit homepage to get cookies
            session.get("https://www.seek.com.au/", headers=HEADERS, timeout=10)
            time.sleep(1)
            resp = session.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                return resp.text
        else:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  Error: {e}", file=sys.stderr)
    return ""


def parse_seek_html(html, keyword):
    """Parse Seek search results from HTML."""
    jobs = []

    # Try to extract from __NEXT_DATA__ or JSON-LD
    next_data = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if next_data:
        try:
            data = json.loads(next_data.group(1))
            # Navigate the Next.js data structure
            props = data.get("props", {}).get("pageProps", {})
            results = props.get("searchResults", props.get("initialState", {}).get("jobSearch", {}).get("results", []))
            if isinstance(results, dict):
                results = results.get("jobs", results.get("data", []))
            for job in results[:MAX_PER_KEYWORD]:
                if isinstance(job, dict):
                    jobs.append({
                        "title": job.get("title", ""),
                        "company": job.get("advertiser", job.get("company", "")),
                        "url": f"https://www.seek.com.au/job/{job.get('id', '')}",
                        "location": job.get("location", job.get("area", "")),
                        "posted": job.get("listingDate", "")[:10],
                        "source": "Seek",
                        "salary": job.get("salary", ""),
                        "description": job.get("teaser", "")[:500],
                        "tags": [keyword.split()[0].lower(), "seek"],
                        "why": f"Seek listing for {job.get('title', '')}",
                        "score": 0,
                        "listing_verification": "seek_verified",
                        "application_route": f"https://www.seek.com.au/job/{job.get('id', '')}",
                        "application_route_type": "seek_direct",
                        "remote": "remote" in job.get("title", "").lower(),
                    })
            if jobs:
                return jobs
        except:
            pass

    # Fallback: regex extraction
    title_pattern = re.compile(r'<a[^>]*href="/job/(\d+)"[^>]*>\s*<h2[^>]*>(.*?)</h2>', re.DOTALL)
    for match in title_pattern.finditer(html):
        job_id, title = match.groups()
        title = re.sub(r'<[^>]+>', '', title).strip()
        # Find company near this job
        start_pos = match.end()
        company_match = re.search(r'<span[^>]*>(.*?)</span>', html[start_pos:start_pos+500])
        company = re.sub(r'<[^>]+>', '', company_match.group(1)).strip() if company_match else ""

        jobs.append({
            "title": title,
            "company": company,
            "url": f"https://www.seek.com.au/job/{job_id}",
            "location": "Melbourne, VIC",
            "posted": "",
            "source": "Seek",
            "salary": "",
            "description": "",
            "tags": [keyword.split()[0].lower(), "seek"],
            "why": f"Seek listing for {title}",
            "score": 0,
            "listing_verification": "seek_verified",
            "application_route": f"https://www.seek.com.au/job/{job_id}",
            "application_route_type": "seek_direct",
            "remote": "remote" in title.lower(),
        })

    return jobs


def scrape_seek():
    """Scrape Seek using API first, fallback to HTML."""
    all_jobs = []
    seen_ids = set()

    for keyword in IT_KEYWORDS:
        print(f"  Searching: {keyword}...")
        collected = 0

        # Try API first
        data = fetch_seek_api(keyword)
        if data and data.get("jobs"):
            for job in data["jobs"][:MAX_PER_KEYWORD]:
                job_id = job.get("id", "")
                if job_id in seen_ids:
                    continue
                seen_ids.add(job_id)
                all_jobs.append({
                    "title": job.get("title", ""),
                    "company": job.get("advertiser", {}).get("description", ""),
                    "url": f"https://www.seek.com.au/job/{job_id}",
                    "location": job.get("places", {}).get("label", "Melbourne, VIC"),
                    "posted": job.get("listingDate", "")[:10],
                    "source": "Seek",
                    "salary": job.get("salaryLabel", ""),
                    "description": job.get("teaser", "")[:500],
                    "tags": [keyword.split()[0].lower(), "seek"],
                    "why": f"Seek listing for {job.get('title', '')}",
                    "score": 0,
                    "listing_verification": "seek_verified",
                    "application_route": f"https://www.seek.com.au/job/{job_id}",
                    "application_route_type": "seek_direct",
                    "remote": any(t.get("label", "").lower() == "remote" for t in job.get("workType", [])),
                })
                collected += 1
            print(f"    API: {collected} jobs")
        else:
            # Fallback to HTML
            html = fetch_seek_page(keyword)
            if html:
                jobs = parse_seek_html(html, keyword)
                for job in jobs[:MAX_PER_KEYWORD]:
                    job_id = job["url"].split("/job/")[-1].split("?")[0]
                    if job_id in seen_ids:
                        continue
                    seen_ids.add(job_id)
                    all_jobs.append(job)
                    collected += 1
                print(f"    HTML: {collected} jobs")
            else:
                print(f"    Failed")

        time.sleep(2)

    return all_jobs


def main():
    output_dir = Path(__file__).parent
    output_path = output_dir / "jobs_seek_requests.json"

    print("Scraping Seek with requests + browser headers...")
    jobs = scrape_seek()

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"source": "seek_requests", "scraped_at": datetime.now(timezone.utc).isoformat(), "count": len(jobs), "jobs": jobs}, f, indent=2, ensure_ascii=False)

    print(f"\nSeek (requests): {len(jobs)} jobs -> {output_path.name}")
    return jobs


if __name__ == "__main__":
    main()
