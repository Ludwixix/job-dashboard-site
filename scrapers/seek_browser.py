#!/usr/bin/env python3
"""
Browser-based Seek scraper using Playwright.
Bypasses Cloudflare and anti-bot protection by running a real Chromium browser.
"""
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Install playwright: pip3 install playwright && playwright install chromium")
    sys.exit(1)

IT_KEYWORDS = [
    "IT support Melbourne", "system administrator Melbourne",
    "network engineer Melbourne", "cloud engineer Melbourne",
    "devops engineer Melbourne", "cyber security Melbourne",
    "software engineer Melbourne", "data engineer Melbourne",
    "service desk Melbourne", "help desk Melbourne",
    "desktop support Melbourne", "microsoft 365 Melbourne",
    "azure engineer Melbourne", "intune Melbourne",
    "windows server Melbourne", "linux administrator Melbourne",
    "kubernetes Melbourne", "terraform Melbourne",
    "infrastructure engineer Melbourne", "endpoint engineer Melbourne",
    "project manager IT Melbourne", "VMware Melbourne",
]

MAX_PER_KEYWORD = 25


def scrape_seek_browser():
    """Scrape Seek using Playwright browser to bypass Cloudflare."""
    all_jobs = []
    seen_ids = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="en-AU",
        )
        # Remove webdriver flag
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        page = context.new_page()

        for keyword in IT_KEYWORDS:
            print(f"  Searching: {keyword}...")
            collected = 0

            try:
                # Navigate to Seek search
                search_url = f"https://www.seek.com.au/{keyword.replace(' ', '-')}-jobs/in-All-Melbourne-VIC"
                page.goto(search_url, wait_until="domcontentloaded", timeout=30000)

                # Wait for Cloudflare challenge if present
                time.sleep(3)

                # Try to wait for job cards to load
                try:
                    page.wait_for_selector('[data-testid="job-card"], article[data-job-id], a[href*="/job/"]', timeout=15000)
                except:
                    print(f"    No job cards found, trying alternative selectors...")
                    try:
                        page.wait_for_selector('.job-listing, .search-results, [class*="job"]', timeout=10000)
                    except:
                        print(f"    Page didn't load properly, skipping")
                        continue

                # Extract jobs from the page
                jobs_data = page.evaluate("""() => {
                    const jobs = [];
                    // Try multiple selector strategies
                    const cards = document.querySelectorAll('[data-testid="job-card"], article[data-job-id], .job-listing, [class*="JobCard"]');
                    cards.forEach(card => {
                        const titleEl = card.querySelector('a[data-testid="job-title"], h3 a, [class*="title"] a');
                        const companyEl = card.querySelector('[data-testid="job-company"], [class*="company"], [class*="advertiser"]');
                        const locationEl = card.querySelector('[data-testid="job-location"], [class*="location"]');
                        const linkEl = card.querySelector('a[href*="/job/"]');
                        const salaryEl = card.querySelector('[class*="salary"], [data-testid*="salary"]');

                        if (titleEl && linkEl) {
                            jobs.push({
                                title: titleEl.textContent.trim(),
                                company: companyEl ? companyEl.textContent.trim() : '',
                                location: locationEl ? locationEl.textContent.trim() : '',
                                url: linkEl.href.startsWith('http') ? linkEl.href : 'https://www.seek.com.au' + linkEl.getAttribute('href'),
                                salary: salaryEl ? salaryEl.textContent.trim() : '',
                            });
                        }
                    });
                    return jobs;
                }""")

                for job in jobs_data:
                    job_id = job.get("url", "").split("/job/")[-1].split("?")[0] if "/job/" in job.get("url", "") else job.get("url", "")
                    if job_id in seen_ids:
                        continue
                    seen_ids.add(job_id)

                    all_jobs.append({
                        "title": job.get("title", ""),
                        "company": job.get("company", ""),
                        "url": job.get("url", ""),
                        "location": job.get("location", "Melbourne, VIC"),
                        "posted": "",
                        "source": "Seek",
                        "salary": job.get("salary", ""),
                        "description": "",
                        "tags": [keyword.split()[0].lower(), "seek"],
                        "why": f"Seek listing for {job.get('title', '')} at {job.get('company', '')}",
                        "score": 0,
                        "listing_verification": "seek_verified",
                        "application_route": job.get("url", ""),
                        "application_route_type": "seek_direct",
                        "remote": "remote" in job.get("title", "").lower(),
                    })
                    collected += 1
                    if collected >= MAX_PER_KEYWORD:
                        break

                print(f"    -> {collected} jobs")

            except Exception as e:
                print(f"    Error: {e}")

            time.sleep(2)  # Rate limit

        browser.close()

    return all_jobs


def main():
    output_dir = Path(__file__).parent
    output_path = output_dir / "jobs_seek_browser.json"

    print("Scraping Seek with Playwright browser...")
    jobs = scrape_seek_browser()

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"source": "seek_browser", "scraped_at": datetime.now(timezone.utc).isoformat(), "count": len(jobs), "jobs": jobs}, f, indent=2, ensure_ascii=False)

    print(f"\nSeek (browser): {len(jobs)} jobs -> {output_path.name}")
    return jobs


if __name__ == "__main__":
    main()
