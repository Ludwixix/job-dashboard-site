#!/usr/bin/env python3
"""
LinkedIn job scraper using Playwright.
Uses LinkedIn's public job search (no login required) to find roles.
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
    "IT support Melbourne",
    "system administrator Melbourne",
    "network engineer Melbourne",
    "cloud engineer Melbourne",
    "devops engineer Melbourne",
    "cyber security Melbourne",
    "software engineer Melbourne",
    "data engineer Melbourne",
    "service desk Melbourne",
    "help desk Melbourne",
    "desktop support Melbourne",
    "microsoft 365 Melbourne",
    "azure engineer Melbourne",
    "intune Melbourne",
    "windows server Melbourne",
    "linux administrator Melbourne",
    "kubernetes Melbourne",
    "terraform Melbourne",
    "infrastructure engineer Melbourne",
    "endpoint engineer Melbourne",
    "project manager IT Melbourne",
    "platform engineer Melbourne",
    "Entra ID Melbourne",
    "PowerShell Melbourne",
]

# Additional keywords for Bridge/Local and Trades streams
BRIDGE_KEYWORDS = [
    "casual work Melbourne",
    "part time retail Melbourne",
    "warehouse Melbourne",
    "courier Melbourne",
    "hospitality Melbourne",
    "barista Melbourne",
]

TRADE_KEYWORDS = [
    "traineeship Melbourne",
    "apprenticeship Melbourne",
    "data centre technician Melbourne",
    "cabling technician Melbourne",
    "telecommunications Melbourne",
]

MAX_PER_KEYWORD = 25
MAX_PAGES = 4  # LinkedIn shows ~25 results per page, 4 pages = 100 max


def scrape_linkedin_browser():
    """Scrape LinkedIn public job search using Playwright."""
    all_jobs = []
    seen_urls = set()
    all_keywords = IT_KEYWORDS + BRIDGE_KEYWORDS + TRADE_KEYWORDS

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
            ],
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="en-AU",
        )
        # Remove webdriver flag
        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        page = context.new_page()

        for keyword in all_keywords:
            print(f"  Searching: {keyword}...")
            collected = 0

            for page_num in range(MAX_PAGES):
                try:
                    # LinkedIn public search URL (no login required)
                    encoded_kw = keyword.replace(" ", "%20")
                    search_url = (
                        f"https://www.linkedin.com/jobs/search/"
                        f"?keywords={encoded_kw}"
                        f"&location=Melbourne%2C%20Victoria%2C%20Australia"
                        f"&f_TPR=r604800"  # Last week
                        f"&start={page_num * 25}"
                    )

                    page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
                    time.sleep(3)

                    # Extract jobs via page evaluation
                    jobs_data = page.evaluate(
                        """() => {
                        const jobs = [];
                        const cards = document.querySelectorAll('.base-search-card');
                        cards.forEach(card => {
                            const titleEl = card.querySelector('.base-search-card__title');
                            const companyEl = card.querySelector('.base-search-card__subtitle a');
                            const locationEl = card.querySelector('.job-search-card__location');
                            const linkEl = card.querySelector('a[href*="linkedin.com/jobs/view/"]');
                            const dateEl = card.querySelector('time');
                            const dateRelative = card.querySelector('.date');

                            if (titleEl && linkEl) {
                                let url = linkEl.href || '';
                                // Clean up URL tracking params
                                url = url.split('?')[0];

                                jobs.push({
                                    title: titleEl.textContent.trim(),
                                    company: companyEl ? companyEl.textContent.trim() : '',
                                    location: locationEl ? locationEl.textContent.trim() : '',
                                    url: url,
                                    posted: dateEl ? dateEl.getAttribute('datetime') || '' : '',
                                    posted_relative: dateRelative ? dateRelative.textContent.trim() : '',
                                });
                            }
                        });
                        return jobs;
                    }"""
                    )

                    if not jobs_data:
                        break  # No more results

                    for job in jobs_data:
                        url = job.get("url", "")
                        if url in seen_urls:
                            continue
                        seen_urls.add(url)

                        # Determine stream based on keyword
                        stream = "Core IT"
                        if any(k.lower().split()[0] in keyword.lower() for k in BRIDGE_KEYWORDS):
                            stream = "Local Bridge"
                        elif any(k.lower().split()[0] in keyword.lower() for k in TRADE_KEYWORDS):
                            stream = "Trade Pathways"

                        all_jobs.append(
                            {
                                "title": job.get("title", ""),
                                "company": job.get("company", ""),
                                "url": url,
                                "location": job.get("location", "Melbourne, VIC"),
                                "posted": job.get("posted", "")[:10],
                                "source": "LinkedIn",
                                "salary": "",
                                "description": "",
                                "tags": [keyword.split()[0].lower(), "linkedin", stream.lower().replace(" ", "_")],
                                "why": f"LinkedIn listing for {job.get('title', '')} at {job.get('company', '')}",
                                "score": 0,
                                "listing_verification": "linkedin_public",
                                "application_route": url,
                                "application_route_type": "linkedin_direct",
                                "remote": "remote" in job.get("title", "").lower()
                                or "remote" in job.get("location", "").lower(),
                                "stream": stream,
                            }
                        )
                        collected += 1
                        if collected >= MAX_PER_KEYWORD:
                            break

                    if collected >= MAX_PER_KEYWORD:
                        break

                    time.sleep(2)  # Rate limit between pages

                except Exception as e:
                    print(f"    Error on page {page_num}: {e}")
                    break

            print(f"    -> {collected} jobs")
            time.sleep(2)  # Rate limit between keywords

        browser.close()

    return all_jobs


def main():
    output_dir = Path(__file__).parent
    output_path = output_dir / "jobs_linkedin.json"

    print("Scraping LinkedIn public job search...")
    jobs = scrape_linkedin_browser()

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "source": "linkedin",
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                "count": len(jobs),
                "jobs": jobs,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(f"\nLinkedIn: {len(jobs)} jobs -> {output_path.name}")
    return jobs


if __name__ == "__main__":
    main()
