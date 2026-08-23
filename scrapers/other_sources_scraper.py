#!/usr/bin/env python3
"""
Additional job sources: Jora, CareerOne, and RSS feeds.
These are fallback sources when Seek/Indeed block scraping.
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/html, application/xml, */*",
}


def scrape_jora():
    """Scrape Jora.com.au (Australian job aggregator)."""
    print("  Scraping Jora...")
    jobs = []
    keywords = ["IT support", "system administrator", "cloud engineer", "devops", "cyber security"]

    for kw in keywords:
        params = urllib.parse.urlencode({"q": kw, "l": "Melbourne+VIC", "sp": "freelancer"})
        url = f"https://au.jora.com/j?sp=search&q={params}"
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode("utf-8", errors="replace")

            # Parse Jora job cards
            pattern = re.compile(
                r'<h2[^>]*class="job-title"[^>]*>\s*<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>.*?'
                r'<span[^>]*class="company"[^>]*>(.*?)</span>',
                re.DOTALL
            )
            for match in pattern.finditer(html):
                url_path, title, company = match.groups()
                title = re.sub(r'<[^>]+>', '', title).strip()
                company = re.sub(r'<[^>]+>', '', company).strip()
                full_url = f"https://au.jora.com{url_path}" if url_path.startswith("/") else url_path
                jobs.append({
                    "title": title, "company": company, "url": full_url,
                    "location": "Melbourne, VIC", "posted": "", "source": "Jora",
                    "salary": "", "description": "",
                    "tags": [kw, "jora"],
                    "why": f"Jora listing for {title} at {company}",
                    "score": 0, "listing_verification": "web_scraped",
                    "application_route": full_url, "application_route_type": "jora_direct",
                    "remote": "remote" in title.lower(),
                })
            time.sleep(1)
        except Exception as e:
            print(f"    Error: {e}", file=sys.stderr)

    print(f"    -> {len(jobs)} jobs")
    return jobs


def scrape_careerone():
    """Scrape CareerOne.com.au (Australian job board)."""
    print("  Scraping CareerOne...")
    jobs = []
    keywords = ["IT support", "system administrator", "cloud engineer", "devops"]

    for kw in keywords:
        params = urllib.parse.urlencode({"Keywords": kw, "Location": "Melbourne"})
        url = f"https://www.careerone.com.au/jobs?{params}"
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode("utf-8", errors="replace")

            pattern = re.compile(
                r'<h3[^>]*class="job-title"[^>]*>\s*<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>.*?'
                r'<span[^>]*class="company"[^>]*>(.*?)</span>',
                re.DOTALL
            )
            for match in pattern.finditer(html):
                url_path, title, company = match.groups()
                title = re.sub(r'<[^>]+>', '', title).strip()
                company = re.sub(r'<[^>]+>', '', company).strip()
                full_url = f"https://www.careerone.com.au{url_path}" if url_path.startswith("/") else url_path
                jobs.append({
                    "title": title, "company": company, "url": full_url,
                    "location": "Melbourne, VIC", "posted": "", "source": "CareerOne",
                    "salary": "", "description": "",
                    "tags": [kw, "careerone"],
                    "why": f"CareerOne listing for {title} at {company}",
                    "score": 0, "listing_verification": "web_scraped",
                    "application_route": full_url, "application_route_type": "careerone_direct",
                    "remote": "remote" in title.lower(),
                })
            time.sleep(1)
        except Exception as e:
            print(f"    Error: {e}", file=sys.stderr)

    print(f"    -> {len(jobs)} jobs")
    return jobs


def scrape_rss_feeds():
    """Scrape RSS feeds from major Australian employers."""
    print("  Scraping RSS feeds...")
    jobs = []
    feeds = [
        ("https://www.seek.com.au/job/rss?keywords=IT&location=Melbourne", "Seek RSS"),
    ]

    for feed_url, source in feeds:
        try:
            req = urllib.request.Request(feed_url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15) as resp:
                xml = resp.read().decode("utf-8", errors="replace")

            # Parse RSS/Atom
            items = re.findall(r'<item>(.*?)</item>', xml, re.DOTALL)
            for item in items:
                title = re.search(r'<title>(.*?)</title>', item)
                link = re.search(r'<link>(.*?)</link>', item)
                pubdate = re.search(r'<pubDate>(.*?)</pubDate>', item)
                if title and link:
                    jobs.append({
                        "title": re.sub(r'<[^>]+>', '', title.group(1)).strip(),
                        "company": "",
                        "url": link.group(1).strip(),
                        "location": "Melbourne, VIC",
                        "posted": pubdate.group(1)[:10] if pubdate else "",
                        "source": source,
                        "salary": "",
                        "description": "",
                        "tags": ["rss", source.lower().replace(" ", "_")],
                        "why": "RSS feed listing",
                        "score": 0,
                        "listing_verification": "rss_feed",
                        "application_route": link.group(1).strip(),
                        "application_route_type": "rss_direct",
                        "remote": False,
                    })
            time.sleep(1)
        except Exception as e:
            print(f"    Error: {e}", file=sys.stderr)

    print(f"    -> {len(jobs)} jobs")
    return jobs


def main():
    output_dir = Path(__file__).parent
    output_path = output_dir / "jobs_other_sources.json"

    print("Scraping additional sources...")
    all_jobs = []
    all_jobs.extend(scrape_jora())
    all_jobs.extend(scrape_careerone())
    all_jobs.extend(scrape_rss_feeds())

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"source": "other", "scraped_at": datetime.now(timezone.utc).isoformat(), "count": len(all_jobs), "jobs": all_jobs}, f, indent=2, ensure_ascii=False)

    print(f"\nOther sources: {len(all_jobs)} jobs -> {output_path.name}")
    return all_jobs


if __name__ == "__main__":
    main()
