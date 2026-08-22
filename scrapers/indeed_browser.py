#!/usr/bin/env python3
"""
Browser-based Indeed scraper using Playwright.
Bypasses anti-bot protection by running a real Chromium browser.
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
    "IT support", "system administrator", "network engineer",
    "cloud engineer", "devops", "cyber security", "software engineer",
    "data engineer", "service desk", "help desk", "desktop support",
    "microsoft 365", "azure", "intune", "windows server", "linux admin",
    "infrastructure engineer", "endpoint engineer",
]

MAX_PER_KEYWORD = 25


def scrape_indeed_browser():
    """Scrape Indeed using Playwright browser to bypass anti-bot."""
    all_jobs = []
    seen_urls = set()

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
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        page = context.new_page()

        for keyword in IT_KEYWORDS:
            print(f"  Searching: {keyword}...")
            collected = 0

            try:
                search_url = f"https://au.indeed.com/jobs?q={keyword.replace(' ', '+')}&l=Melbourne%2C+VIC&sort=date&fromage=14"
                page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(3)

                # Wait for job cards
                try:
                    page.wait_for_selector('.jobsearch-ResultsList, .job_seen_beacon, .jobsearch-ResultsList .result', timeout=15000)
                except:
                    print(f"    No results loaded, skipping")
                    continue

                # Extract jobs
                jobs_data = page.evaluate("""() => {
                    const jobs = [];
                    // Indeed uses various selectors
                    const cards = document.querySelectorAll('.jobsearch-ResultsList .result, .job_seen_beacon, [class*="job"][class*="result"], .resultContent');
                    cards.forEach(card => {
                        const titleEl = card.querySelector('h2.jobTitle a, a.jcs-JobTitle, [class*="jobTitle"] a');
                        const companyEl = card.querySelector('.companyName, .company_location .companyName, [data-testid="company-name"]');
                        const locationEl = card.querySelector('.companyLocation, .company_location .companyLocation, [data-testid="text-location"]');
                        const salaryEl = card.querySelector('.salary-snippet-container, [class*="salary"]');

                        if (titleEl) {
                            const href = titleEl.getAttribute('href') || '';
                            const url = href.startsWith('http') ? href : 'https://au.indeed.com' + href;
                            jobs.push({
                                title: titleEl.textContent.trim(),
                                company: companyEl ? companyEl.textContent.trim() : '',
                                location: locationEl ? locationEl.textContent.trim() : '',
                                url: url,
                                salary: salaryEl ? salaryEl.textContent.trim() : '',
                            });
                        }
                    });
                    return jobs;
                }""")

                for job in jobs_data:
                    if job.get("url", "") in seen_urls:
                        continue
                    seen_urls.add(job.get("url", ""))

                    all_jobs.append({
                        "title": job.get("title", ""),
                        "company": job.get("company", ""),
                        "url": job.get("url", ""),
                        "location": job.get("location", "Melbourne, VIC"),
                        "posted": "",
                        "source": "Indeed",
                        "salary": job.get("salary", ""),
                        "description": "",
                        "tags": [keyword.split()[0].lower(), "indeed"],
                        "why": f"Indeed listing for {job.get('title', '')} at {job.get('company', '')}",
                        "score": 0,
                        "listing_verification": "web_scraped",
                        "application_route": job.get("url", ""),
                        "application_route_type": "indeed_direct",
                        "remote": "remote" in job.get("title", "").lower(),
                    })
                    collected += 1
                    if collected >= MAX_PER_KEYWORD:
                        break

                print(f"    -> {collected} jobs")

            except Exception as e:
                print(f"    Error: {e}")

            time.sleep(2)

        browser.close()

    return all_jobs


def main():
    output_dir = Path(__file__).parent
    output_path = output_dir / "jobs_indeed_browser.json"

    print("Scraping Indeed with Playwright browser...")
    jobs = scrape_indeed_browser()

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"source": "indeed_browser", "scraped_at": datetime.now(timezone.utc).isoformat(), "count": len(jobs), "jobs": jobs}, f, indent=2, ensure_ascii=False)

    print(f"\nIndeed (browser): {len(jobs)} jobs -> {output_path.name}")
    return jobs


if __name__ == "__main__":
    main()
