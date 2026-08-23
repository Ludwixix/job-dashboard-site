#!/usr/bin/env python3
"""
Browser-based Seek scraper using Playwright.
Bypasses Cloudflare and anti-bot protection by running a real Chromium browser.

Selectors updated 2026-08-23 based on live Seek DOM inspection.
Uses data-automation attributes (stable) as primary, data-testid as fallback.
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

# ── Search keywords (3-stream aware) ──────────────────────────────────────
# Stream 1: Core IT & Systems Engineering
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
    "platform engineer Melbourne", "data centre Melbourne",
]

MAX_PER_KEYWORD = 25

# ── JavaScript extraction (single page) ──────────────────────────────────
# Updated selectors based on 2026-08-23 DOM inspection:
#   Card:     [data-testid="job-card"]
#   Title:    [data-testid="job-card-title"]   (inside h3)
#   Company:  [data-automation="jobCompany"]
#   Location: [data-automation="jobLocation"]
#   Salary:   [data-automation="jobSalary"]
#   Desc:     [data-automation="jobShortDescription"]
#   Posted:   [data-automation="jobListingDate"]
#   Link:     [data-automation="jobTitle"] (a tag with href)
#   Job ID:   data-job-id attribute on card

EXTRACT_JS = """() => {
    const jobs = [];
    const cards = document.querySelectorAll('[data-testid="job-card"]');
    cards.forEach(card => {
        // Title
        const titleEl = card.querySelector('[data-testid="job-card-title"]');
        // Company
        const companyEl = card.querySelector('[data-automation="jobCompany"]');
        // Location
        const locationEl = card.querySelector('[data-automation="jobLocation"]');
        // Salary
        const salaryEl = card.querySelector('[data-automation="jobSalary"]');
        // Description teaser
        const descEl = card.querySelector('[data-automation="jobShortDescription"]');
        // Posted date
        const dateEl = card.querySelector('[data-automation="jobListingDate"]');
        // Link (use the title link for a clean URL)
        const linkEl = card.querySelector('[data-automation="jobTitle"]');
        // Job ID
        const jobId = card.getAttribute('data-job-id') || '';
        // Classification
        const classEl = card.querySelector('[data-automation="jobClassification"]');
        const subClassEl = card.querySelector('[data-automation="jobSubClassification"]');

        // Work arrangement: check card text for (Remote), (Hybrid), (Onsite)
        let workArrangement = 'Onsite';
        const cardText = card.textContent || '';
        if (/\\(Remote\\)/i.test(cardText)) workArrangement = 'Remote';
        else if (/\\(Hybrid\\)/i.test(cardText)) workArrangement = 'Hybrid';

        if (titleEl) {
            const href = linkEl ? linkEl.getAttribute('href') : '';
            const url = href.startsWith('http') ? href : (href ? 'https://au.seek.com' + href : '');

            jobs.push({
                title: titleEl.textContent.trim(),
                company: companyEl ? companyEl.textContent.trim() : '',
                location: locationEl ? locationEl.textContent.trim() : '',
                salary: salaryEl ? salaryEl.textContent.trim() : '',
                description: descEl ? descEl.textContent.trim() : '',
                posted: dateEl ? dateEl.textContent.trim() : '',
                url: url,
                jobId: jobId,
                classification: classEl ? classEl.textContent.trim() : '',
                subClassification: subClassEl ? subClassEl.textContent.trim() : '',
                workArrangement: workArrangement,
            });
        }
    });
    return jobs;
}"""


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
        # Remove webdriver flag to avoid detection
        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        page = context.new_page()

        for keyword in IT_KEYWORDS:
            print(f"  Searching: {keyword}...")
            collected = 0

            try:
                # Build search URL
                slug = keyword.replace(" ", "-")
                search_url = f"https://au.seek.com/{slug}-jobs/in-Melbourne-VIC"
                page.goto(search_url, wait_until="domcontentloaded", timeout=30000)

                # Wait for Cloudflare challenge to settle
                time.sleep(4)

                # Wait for job cards to appear
                try:
                    page.wait_for_selector(
                        '[data-testid="job-card"]',
                        timeout=15000,
                    )
                except Exception:
                    print(f"    No job cards found, skipping")
                    continue

                # Small extra wait for dynamic content
                time.sleep(1)

                # Extract jobs
                jobs_data = page.evaluate(EXTRACT_JS)

                for job in jobs_data:
                    # Dedup by job ID or URL
                    dedup_key = job.get("jobId") or job.get("url", "")
                    if dedup_key in seen_ids:
                        continue
                    seen_ids.add(dedup_key)

                    # Determine remote status from work arrangement
                    is_remote = job.get("workArrangement", "").lower() == "remote"

                    all_jobs.append({
                        "title": job.get("title", ""),
                        "company": job.get("company", ""),
                        "url": job.get("url", ""),
                        "location": job.get("location", "Melbourne, VIC"),
                        "posted": job.get("posted", ""),
                        "source": "Seek",
                        "salary": job.get("salary", ""),
                        "description": job.get("description", ""),
                        "tags": [
                            keyword.split()[0].lower(),
                            "seek",
                        ],
                        "why": f"Seek listing for {job.get('title', '')} at {job.get('company', '')}",
                        "score": 0,
                        "listing_verification": "seek_verified",
                        "application_route": job.get("url", ""),
                        "application_route_type": "seek_direct",
                        "remote": is_remote,
                        "work_arrangement": job.get("workArrangement", "Onsite"),
                        "classification": job.get("classification", ""),
                        "sub_classification": job.get("subClassification", ""),
                    })
                    collected += 1
                    if collected >= MAX_PER_KEYWORD:
                        break

                print(f"    -> {collected} jobs")

            except Exception as e:
                print(f"    Error: {e}")

            # Rate limit: 2-3 seconds between requests
            time.sleep(2.5)

        browser.close()

    return all_jobs


def main():
    output_dir = Path(__file__).parent
    output_path = output_dir / "jobs_seek_browser.json"

    print("Scraping Seek with Playwright browser...")
    jobs = scrape_seek_browser()

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "source": "seek_browser",
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "count": len(jobs),
            "jobs": jobs,
        }, f, indent=2, ensure_ascii=False)

    print(f"\nSeek (browser): {len(jobs)} jobs -> {output_path.name}")

    # Quick quality check
    has_company = sum(1 for j in jobs if j.get("company"))
    has_location = sum(1 for j in jobs if j.get("location"))
    has_salary = sum(1 for j in jobs if j.get("salary"))
    print(f"  Quality: {has_company}/{len(jobs)} have company, "
          f"{has_location}/{len(jobs)} have location, "
          f"{has_salary}/{len(jobs)} have salary")

    return jobs


if __name__ == "__main__":
    main()
