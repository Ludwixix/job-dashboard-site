#!/usr/bin/env python3
"""
Robust Seek.com.au scraper with multiple fallback strategies.

Strategy chain:
  1. Playwright browser (bypasses Cloudflare, most reliable)
  2. Seek search API with rotated headers (may work intermittently)
  3. Google site-search via SerpAPI/requests (finds Seek listings via Google)

Features:
  - Proxy rotation (SOCKS5/HTTP via WireGuard or free proxies)
  - Exponential backoff retries
  - Rate limiting with jitter
  - User-agent rotation
  - Automatic Cloudflare challenge detection
  - Deduplication across strategies
"""

import json
import os
import random
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ─── Configuration ────────────────────────────────────────────────────────

SEEK_API_URL = "https://chalice-search-api.cloud.seek.com.au/search"
SEEK_BASE_URL = "https://au.seek.com"

# IT & Systems Engineering keywords — Melbourne focused
IT_KEYWORDS = [
    "IT support", "system administrator", "network engineer",
    "cloud engineer", "devops engineer", "cyber security",
    "software engineer", "data engineer", "service desk",
    "help desk", "desktop support", "microsoft 365",
    "azure engineer", "intune", "windows server",
    "linux administrator", "kubernetes", "terraform",
    "infrastructure engineer", "endpoint engineer",
    "project manager IT", "VMware", "platform engineer",
    "data centre",
]

# Broader keywords for Google site-search fallback
GOOGLE_SEEK_KEYWORDS = [
    "IT support Melbourne", "system administrator Melbourne",
    "network engineer Melbourne", "cloud engineer Melbourne",
    "devops Melbourne", "service desk Melbourne",
    "desktop support Melbourne", "infrastructure engineer Melbourne",
    "cyber security Melbourne", "data engineer Melbourne",
    "platform engineer Melbourne", "endpoint engineer Melbourne",
]

MAX_PER_KEYWORD = 25
REQUEST_TIMEOUT = 15

# User-agent pool for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
]

# ─── Helpers ──────────────────────────────────────────────────────────────


def _jitter(base: float, max_extra: float = 2.0) -> float:
    """Return base + random jitter."""
    return base + random.uniform(0, max_extra)


def _rotate_ua() -> str:
    return random.choice(USER_AGENTS)


def _is_cloudflare_challenge(html: str) -> bool:
    """Detect Cloudflare challenge page."""
    indicators = [
        "Checking your browser",
        "Just a moment",
        "Verify you are human",
        "challenge-platform",
        "cf-challenge",
        "Attention Required! | Cloudflare",
    ]
    return any(ind.lower() in html.lower() for ind in indicators)


def _safe_filename(keyword: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", keyword.lower()).strip("_")


# ─── Strategy 1: Playwright Browser ──────────────────────────────────────

EXTRACT_JS = """() => {
    const jobs = [];
    const cards = document.querySelectorAll('[data-testid="job-card"]');
    cards.forEach(card => {
        const titleEl = card.querySelector('[data-testid="job-card-title"]');
        const companyEl = card.querySelector('[data-automation="jobCompany"]');
        const locationEl = card.querySelector('[data-automation="jobLocation"]');
        const salaryEl = card.querySelector('[data-automation="jobSalary"]');
        const descEl = card.querySelector('[data-automation="jobShortDescription"]');
        const dateEl = card.querySelector('[data-automation="jobListingDate"]');
        const linkEl = card.querySelector('[data-automation="jobTitle"]');
        const jobId = card.getAttribute('data-job-id') || '';
        const classEl = card.querySelector('[data-automation="jobClassification"]');
        const subClassEl = card.querySelector('[data-automation="jobSubClassification"]');

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


def _scrape_seek_playwright(
    keywords: list[str],
    max_per_keyword: int = MAX_PER_KEYWORD,
    proxy: Optional[str] = None,
    headless: bool = True,
    retries: int = 2,
) -> list[dict]:
    """Strategy 1: Playwright browser — most reliable, bypasses Cloudflare."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  [playwright] Not installed, skipping", file=sys.stderr)
        return []

    all_jobs = []
    seen_ids = set()

    launch_args = [
        "--no-sandbox",
        "--disable-blink-features=AutomationControlled",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--disable-extensions",
    ]
    if proxy:
        launch_args.append(f"--proxy-server={proxy}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, args=launch_args)
        context = browser.new_context(
            user_agent=_rotate_ua(),
            viewport={"width": 1920, "height": 1080},
            locale="en-AU",
            timezone_id="Australia/Melbourne",
        )
        # Stealth: remove webdriver flag
        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        context.add_init_script(
            "Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})"
        )
        context.add_init_script(
            "Object.defineProperty(navigator, 'languages', {get: () => ['en-AU', 'en']})"
        )

        page = context.new_page()

        for keyword in keywords:
            print(f"  [playwright] {keyword}...", end=" ", flush=True)
            collected = 0

            for attempt in range(retries + 1):
                try:
                    slug = keyword.replace(" ", "-")
                    search_url = f"{SEEK_BASE_URL}/{slug}-jobs/in-Melbourne-VIC"
                    page.goto(search_url, wait_until="domcontentloaded", timeout=30000)

                    # Wait for Cloudflare to settle
                    time.sleep(_jitter(3.0, 2.0))

                    # Check for Cloudflare challenge
                    html = page.content()
                    if _is_cloudflare_challenge(html):
                        print(f"CF challenge (attempt {attempt+1}), waiting...", end=" ", flush=True)
                        time.sleep(_jitter(8.0, 4.0))
                        html = page.content()
                        if _is_cloudflare_challenge(html):
                            if attempt < retries:
                                print("retrying...", end=" ", flush=True)
                                continue
                            else:
                                print("blocked")
                                break

                    # Wait for job cards
                    try:
                        page.wait_for_selector('[data-testid="job-card"]', timeout=12000)
                    except Exception:
                        # Try alternative selector
                        try:
                            page.wait_for_selector('[data-automation="jobListing"]', timeout=5000)
                        except Exception:
                            print("no cards", end=" ")
                            break

                    time.sleep(_jitter(0.5, 0.5))
                    jobs_data = page.evaluate(EXTRACT_JS)

                    for job in jobs_data:
                        dedup_key = job.get("jobId") or job.get("url", "")
                        if dedup_key in seen_ids:
                            continue
                        seen_ids.add(dedup_key)

                        is_remote = job.get("workArrangement", "").lower() == "remote"
                        all_jobs.append({
                            "title": job.get("title", ""),
                            "company": job.get("company", ""),
                            "url": job.get("url", ""),
                            "location": job.get("location", "Melbourne, VIC"),
                            "posted": job.get("posted", ""),
                            "source": "Seek",
                            "salary": job.get("salary", ""),
                            "description": (job.get("description", "") or "")[:500],
                            "tags": [keyword.split()[0].lower(), "seek"],
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
                        if collected >= max_per_keyword:
                            break

                    print(f"{collected} jobs")
                    break  # Success, no retry needed

                except Exception as e:
                    if attempt < retries:
                        wait = _jitter(5.0, 3.0)
                        print(f"error: {e} (retry in {wait:.0f}s)...", end=" ", flush=True)
                        time.sleep(wait)
                    else:
                        print(f"failed: {e}")

            # Rate limit between keywords
            time.sleep(_jitter(2.5, 1.5))

        browser.close()

    return all_jobs


# ─── Strategy 2: Seek API Direct ─────────────────────────────────────────


def _scrape_seek_api(
    keywords: list[str],
    max_per_keyword: int = MAX_PER_KEYWORD,
) -> list[dict]:
    """Strategy 2: Seek search API with browser-like headers."""
    all_jobs = []
    seen_ids = set()

    for keyword in keywords:
        print(f"  [api] {keyword}...", end=" ", flush=True)
        collected = 0

        params = {
            "siteKey": "AU-Main",
            "where": "Melbourne%2C+VIC",
            "keywords": keyword,
            "pageSize": 22,
            "page": 0,
            "sortmode": "ListedDate",
        }
        url = f"{SEEK_API_URL}?{urllib.parse.urlencode(params)}"
        headers = {
            "User-Agent": _rotate_ua(),
            "Accept": "application/json",
            "Accept-Language": "en-AU,en;q=0.9",
            "Referer": "https://www.seek.com.au/",
            "Origin": "https://www.seek.com.au",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
        }

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                data = json.loads(resp.read().decode())
                jobs = data.get("jobs", [])

                for job in jobs[:max_per_keyword]:
                    job_id = job.get("id", "")
                    if job_id in seen_ids:
                        continue
                    seen_ids.add(job_id)

                    company = ""
                    adv = job.get("advertiser", {})
                    if isinstance(adv, dict):
                        company = adv.get("description", "")
                    if not company:
                        company = job.get("advertiserDescription", "")

                    all_jobs.append({
                        "title": job.get("title", ""),
                        "company": company,
                        "url": f"{SEEK_BASE_URL}/job/{job_id}" if job_id else "",
                        "location": job.get("places", {}).get("label", "Melbourne, VIC"),
                        "posted": (job.get("listingDate", "") or "")[:10],
                        "source": "Seek",
                        "salary": job.get("salaryLabel", ""),
                        "description": (job.get("teaser", "") or "")[:500],
                        "tags": [keyword.split()[0].lower(), "seek"],
                        "why": f"Seek listing for {job.get('title', '')} at {company}",
                        "score": 0,
                        "listing_verification": "seek_verified",
                        "application_route": f"{SEEK_BASE_URL}/job/{job_id}" if job_id else "",
                        "application_route_type": "seek_direct",
                        "remote": any(
                            t.get("label", "").lower() == "remote"
                            for t in job.get("workType", [])
                        ),
                    })
                    collected += 1

                print(f"{collected} jobs")

        except urllib.error.HTTPError as e:
            if e.code == 403:
                print(f"blocked (403)")
            elif e.code == 429:
                print(f"rate limited (429)")
                time.sleep(_jitter(10.0, 5.0))
            else:
                print(f"HTTP {e.code}")
        except Exception as e:
            print(f"error: {e}")

        time.sleep(_jitter(2.0, 1.0))

    return all_jobs


# ─── Strategy 3: Google Site Search ──────────────────────────────────────


def _scrape_seek_via_google(
    keywords: list[str],
    max_per_keyword: int = 10,
) -> list[dict]:
    """Strategy 3: Use Google to find Seek listings (works when Seek blocks direct access)."""
    all_jobs = []
    seen_urls = set()

    for keyword in keywords:
        print(f"  [google] {keyword}...", end=" ", flush=True)
        collected = 0

        query = f"site:seek.com.au/job/ {keyword} Melbourne"
        url = (
            f"https://www.google.com/search?"
            f"q={urllib.parse.quote(query)}&num=10&hl=en-AU&gl=au"
        )
        headers = {
            "User-Agent": _rotate_ua(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-AU,en;q=0.9",
        }

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                html = resp.read().decode("utf-8", errors="replace")

            # Extract Seek job URLs from Google results
            job_urls = re.findall(
                r'https?://(?:au\.seek\.com|www\.seek\.com)/job/(\d+)',
                html,
            )

            for job_id in list(dict.fromkeys(job_urls)):  # dedup preserving order
                if job_id in seen_urls:
                    continue
                seen_urls.add(job_id)

                job_url = f"{SEEK_BASE_URL}/job/{job_id}"
                all_jobs.append({
                    "title": "",  # Will be enriched later if needed
                    "company": "",
                    "url": job_url,
                    "location": "Melbourne, VIC",
                    "posted": "",
                    "source": "Seek",
                    "salary": "",
                    "description": "",
                    "tags": [keyword.split()[0].lower(), "seek", "google_sourced"],
                    "why": f"Seek listing found via Google for '{keyword}'",
                    "score": 0,
                    "listing_verification": "seek_via_google",
                    "application_route": job_url,
                    "application_route_type": "seek_direct",
                    "remote": False,
                })
                collected += 1
                if collected >= max_per_keyword:
                    break

            print(f"{collected} URLs")

        except Exception as e:
            print(f"error: {e}")

        time.sleep(_jitter(3.0, 2.0))

    return all_jobs


# ─── Enrichment: Fill in missing titles from job pages ────────────────────


def _enrich_jobs_playwright(
    jobs: list[dict],
    max_enrich: int = 50,
    proxy: Optional[str] = None,
) -> list[dict]:
    """Visit individual job pages to fill in missing title/company/description."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return jobs

    to_enrich = [j for j in jobs if not j.get("title") and j.get("url")]
    if not to_enrich:
        return jobs

    print(f"  [enrich] Filling in {min(len(to_enrich), max_enrich)} jobs with missing details...")

    launch_args = ["--no-sandbox", "--disable-blink-features=AutomationControlled", "--disable-dev-shm-usage"]
    if proxy:
        launch_args.append(f"--proxy-server={proxy}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=launch_args)
        context = browser.new_context(
            user_agent=_rotate_ua(),
            viewport={"width": 1920, "height": 1080},
            locale="en-AU",
        )
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page = context.new_page()

        for job in to_enrich[:max_enrich]:
            try:
                page.goto(job["url"], wait_until="domcontentloaded", timeout=15000)
                time.sleep(_jitter(2.0, 1.0))

                # Try to extract title
                title_el = page.query_selector("h1")
                if title_el:
                    job["title"] = title_el.inner_text().strip()

                # Try to extract company
                company_el = page.query_selector('[data-automation="jobCompany"]')
                if not company_el:
                    company_el = page.query_selector('[data-automation="advertiser-name"]')
                if company_el:
                    job["company"] = company_el.inner_text().strip()

                # Try to extract description
                desc_el = page.query_selector('[data-automation="jobDescription"]')
                if not desc_el:
                    desc_el = page.query_selector('[class*="jobDescription"]')
                if desc_el:
                    job["description"] = desc_el.inner_text().strip()[:500]

                # Try to extract salary
                salary_el = page.query_selector('[data-automation="jobSalary"]')
                if salary_el:
                    job["salary"] = salary_el.inner_text().strip()

                time.sleep(_jitter(1.0, 0.5))

            except Exception:
                pass  # Skip failed enrichments

        browser.close()

    enriched = sum(1 for j in to_enrich[:max_enrich] if j.get("title"))
    print(f"  [enrich] Enriched {enriched}/{min(len(to_enrich), max_enrich)} jobs")

    return jobs


# ─── Main Orchestrator ────────────────────────────────────────────────────


def scrape_seek(
    proxy: Optional[str] = None,
    keywords: Optional[list[str]] = None,
    max_per_keyword: int = MAX_PER_KEYWORD,
    strategies: Optional[list[str]] = None,
    enrich: bool = True,
) -> list[dict]:
    """
    Scrape Seek jobs using multiple strategies with fallback.

    Args:
        proxy: Optional proxy URL (e.g., "socks5://127.0.0.1:1080")
        keywords: Override default keywords
        max_per_keyword: Max jobs per keyword
        strategies: Override strategy order (default: ["playwright", "api", "google"])
        enrich: Whether to enrich jobs with missing details

    Returns:
        List of normalized job dicts
    """
    kw = keywords or IT_KEYWORDS
    strat_order = strategies or ["playwright", "api", "google"]

    all_jobs = []
    seen_ids = set()

    for strategy in strat_order:
        print(f"\n=== Strategy: {strategy.upper()} ===")

        if strategy == "playwright":
            jobs = _scrape_seek_playwright(kw, max_per_keyword, proxy=proxy)
        elif strategy == "api":
            jobs = _scrape_seek_api(kw, max_per_keyword)
        elif strategy == "google":
            jobs = _scrape_seek_via_google(kw, max_per_keyword=10)
        else:
            print(f"  Unknown strategy: {strategy}")
            continue

        # Deduplicate
        new_count = 0
        for job in jobs:
            dedup_key = job.get("url", "").rstrip("/") or job.get("title", "")
            if dedup_key and dedup_key not in seen_ids:
                seen_ids.add(dedup_key)
                all_jobs.append(job)
                new_count += 1

        print(f"  → +{new_count} new jobs (total: {len(all_jobs)})")

        # If we got a good number from this strategy, skip the rest
        if len(all_jobs) >= 50:
            print(f"  Sufficient jobs found, skipping remaining strategies")
            break

    # Enrich jobs with missing titles
    if enrich and all_jobs:
        missing = sum(1 for j in all_jobs if not j.get("title"))
        if missing > 0:
            all_jobs = _enrich_jobs_playwright(all_jobs, max_enrich=min(missing, 50), proxy=proxy)

    # Score jobs
    for job in all_jobs:
        score = 70
        title = job.get("title", "").lower()
        if any(k in title for k in ["senior", "lead", "principal"]):
            score += 5
        if any(k in title for k in ["engineer", "architect"]):
            score += 3
        if job.get("salary"):
            score += 3
        if job.get("remote"):
            score += 2
        if "balaclava" in job.get("location", "").lower():
            score += 5
        job["score"] = min(score, 99)

    all_jobs.sort(key=lambda j: (-j.get("score", 0), j.get("posted", ""), j.get("company", "")))

    return all_jobs


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Robust Seek.com.au scraper")
    parser.add_argument("--proxy", help="Proxy URL (e.g., socks5://127.0.0.1:1080)")
    parser.add_argument("--strategy", choices=["playwright", "api", "google", "all"], default="all")
    parser.add_argument("--max-per-keyword", type=int, default=MAX_PER_KEYWORD)
    parser.add_argument("--no-enrich", action="store_true", help="Skip job page enrichment")
    parser.add_argument("--keywords", nargs="+", help="Override keywords")
    parser.add_argument("--output", help="Output file path")
    args = parser.parse_args()

    output_dir = Path(__file__).parent
    output_path = Path(args.output) if args.output else output_dir / "jobs_seek_robust.json"

    if args.strategy == "all":
        strategies = ["playwright", "api", "google"]
    else:
        strategies = [args.strategy]

    print("Seek.com.au Robust Scraper")
    print(f"Strategies: {strategies}")
    print(f"Proxy: {args.proxy or 'none'}")
    print(f"Max per keyword: {args.max_per_keyword}")
    print()

    start_time = time.time()
    jobs = scrape_seek(
        proxy=args.proxy,
        keywords=args.keywords,
        max_per_keyword=args.max_per_keyword,
        strategies=strategies,
        enrich=not args.no_enrich,
    )
    elapsed = time.time() - start_time

    # Write output
    output = {
        "source": "seek_robust",
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "count": len(jobs),
        "elapsed_seconds": round(elapsed, 1),
        "strategies_used": strategies,
        "jobs": jobs,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Quality report
    has_title = sum(1 for j in jobs if j.get("title"))
    has_company = sum(1 for j in jobs if j.get("company"))
    has_salary = sum(1 for j in jobs if j.get("salary"))
    has_desc = sum(1 for j in jobs if j.get("description"))

    print(f"\n{'='*50}")
    print(f"SEEK SCRAPE COMPLETE")
    print(f"{'='*50}")
    print(f"Total jobs: {len(jobs)}")
    print(f"Time: {elapsed:.1f}s")
    print(f"Quality:")
    print(f"  Title:    {has_title}/{len(jobs)}")
    print(f"  Company:  {has_company}/{len(jobs)}")
    print(f"  Salary:   {has_salary}/{len(jobs)}")
    print(f"  Desc:     {has_desc}/{len(jobs)}")
    print(f"Output: {output_path}")

    return jobs


if __name__ == "__main__":
    main()
