#!/usr/bin/env python3
"""
Browser-based Indeed scraper using Playwright.

IMPORTANT: Indeed uses Cloudflare Turnstile interactive challenges that block
headless browsers. This scraper attempts multiple strategies but Indeed
scraping is inherently fragile. Use Adzuna/Seek as primary sources.

Strategies tried:
1. Standard headless Chromium with anti-detection
2. Extended wait for Cloudflare challenge resolution
3. Multiple page load attempts with backoff
"""
import json
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

# ── JavaScript extraction ────────────────────────────────────────────────
EXTRACT_JS = """() => {
    const jobs = [];
    // Indeed uses various selector patterns depending on version
    const cards = document.querySelectorAll(
        '.jobsearch-ResultsList .result, ' +
        '.job_seen_beacon, ' +
        '.resultContent, ' +
        '[class*="job"][class*="result"], ' +
        '.job-card-GenericContainer'
    );
    cards.forEach(card => {
        const titleEl = card.querySelector(
            'h2.jobTitle a, a.jcs-JobTitle, [class*="jobTitle"] a, ' +
            '[data-testid="job-title"], h2 a'
        );
        const companyEl = card.querySelector(
            '.companyName, .company_location .companyName, ' +
            '[data-testid="company-name"], .company'
        );
        const locationEl = card.querySelector(
            '.companyLocation, .company_location .companyLocation, ' +
            '[data-testid="text-location"], .location'
        );
        const salaryEl = card.querySelector(
            '.salary-snippet-container, [class*="salary"], ' +
            '[data-testid="attribute_snippet_testid"]'
        );
        const dateEl = card.querySelector(
            '.date, [class*="date"], .new, .myJobsState'
        );
        const descEl = card.querySelector(
            '.jobCardShelfContainer, [class*="shelf"], .job-snippet'
        );

        if (titleEl) {
            const href = titleEl.getAttribute('href') || '';
            const url = href.startsWith('http') ? href : 'https://au.indeed.com' + href;
            jobs.push({
                title: titleEl.textContent.trim(),
                company: companyEl ? companyEl.textContent.trim() : '',
                location: locationEl ? locationEl.textContent.trim() : '',
                url: url,
                salary: salaryEl ? salaryEl.textContent.trim() : '',
                posted: dateEl ? dateEl.textContent.trim() : '',
                description: descEl ? descEl.textContent.trim() : '',
            });
        }
    });
    return jobs;
}"""


def _is_cloudflare_blocked(page_content: str) -> bool:
    """Check if page is a Cloudflare challenge page."""
    indicators = [
        "Additional Verification Required",
        "Just a moment",
        "cf-turnstile",
        "challenge-platform",
        "cf-chl-widget",
    ]
    return any(ind in page_content for ind in indicators)


def _wait_for_content(page, timeout=20):
    """Wait for actual job content to appear, not Cloudflare challenge."""
    for _ in range(timeout // 2):
        time.sleep(2)
        content = page.content()
        if not _is_cloudflare_blocked(content) and "jobsearch" in content.lower():
            return True
    return False


def scrape_indeed_browser():
    """Scrape Indeed using Playwright browser to bypass anti-bot."""
    all_jobs = []
    seen_urls = set()
    cloudflare_blocked = 0

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
        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        page = context.new_page()

        for keyword in IT_KEYWORDS:
            print(f"  Searching: {keyword}...")
            collected = 0

            try:
                search_url = (
                    f"https://au.indeed.com/jobs?"
                    f"q={keyword.replace(' ', '+')}"
                    f"&l=Melbourne%2C+VIC&sort=date&fromage=14"
                )
                page.goto(search_url, wait_until="domcontentloaded", timeout=30000)

                # Wait for content (not Cloudflare challenge)
                content_loaded = _wait_for_content(page, timeout=15)

                if not content_loaded:
                    content = page.content()
                    if _is_cloudflare_blocked(content):
                        cloudflare_blocked += 1
                        print(f"    ⚠ Cloudflare blocked (attempt {cloudflare_blocked})")
                        if cloudflare_blocked >= 3:
                            print("    ⛔ Indeed is consistently blocked by Cloudflare.")
                            print("       Skipping remaining keywords.")
                            break
                    else:
                        print("    No results loaded, skipping")
                    time.sleep(3)
                    continue

                # Reset consecutive block counter on success
                cloudflare_blocked = 0

                # Extract jobs
                jobs_data = page.evaluate(EXTRACT_JS)

                for job in jobs_data:
                    if job.get("url", "") in seen_urls:
                        continue
                    seen_urls.add(job.get("url", ""))

                    all_jobs.append({
                        "title": job.get("title", ""),
                        "company": job.get("company", ""),
                        "url": job.get("url", ""),
                        "location": job.get("location", "Melbourne, VIC"),
                        "posted": job.get("posted", ""),
                        "source": "Indeed",
                        "salary": job.get("salary", ""),
                        "description": job.get("description", ""),
                        "tags": [keyword.split()[0].lower(), "indeed"],
                        "why": f"Indeed listing for {job.get('title', '')} at {job.get('company', '')}",
                        "score": 0,
                        "listing_verification": "web_scraped",
                        "application_route": job.get("url", ""),
                        "application_route_type": "indeed_direct",
                        "remote": "remote" in job.get("title", "").lower(),
                        "work_arrangement": "Remote" if "remote" in job.get("title", "").lower() else "Onsite",
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
    print("⚠ Note: Indeed uses Cloudflare Turnstile which may block headless browsers.")
    jobs = scrape_indeed_browser()

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "source": "indeed_browser",
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "count": len(jobs),
            "jobs": jobs,
        }, f, indent=2, ensure_ascii=False)

    print(f"\nIndeed (browser): {len(jobs)} jobs -> {output_path.name}")

    if len(jobs) == 0:
        print("⚠ Indeed returned 0 jobs. This is likely due to Cloudflare blocking.")
        print("  Adzuna and Seek are the primary reliable sources.")

    return jobs


if __name__ == "__main__":
    main()
