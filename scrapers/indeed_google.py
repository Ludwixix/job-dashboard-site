#!/usr/bin/env python3
"""
Indeed scraper via Google search.
Indeed blocks direct scraping, so we search Google for Indeed listings.
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
    "cloud engineer", "devops", "cyber security",
    "service desk", "help desk", "desktop support",
    "microsoft 365", "azure", "infrastructure engineer",
    "platform engineer", "data engineer",
]

MAX_PER_KEYWORD = 20


def scrape_indeed_via_google():
    """Scrape Indeed listings via Google search results."""
    all_jobs = []
    seen_urls = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
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
            print(f"  Searching Google for: {keyword} indeed...")
            collected = 0

            try:
                query = f"site:au.indeed.com {keyword} Melbourne"
                search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}&num=20"
                page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(3)

                # Extract Indeed job links from Google results
                results = page.evaluate("""() => {
                    const jobs = [];
                    // Google search result links
                    const links = document.querySelectorAll('a[href*="au.indeed.com"]');
                    links.forEach(link => {
                        const href = link.href || '';
                        if (href.includes('/viewjob') || href.includes('/rc/clk')) {
                            // Get the surrounding text for title/company
                            const container = link.closest('.g') || link.parentElement.parentElement;
                            let title = '';
                            let snippet = '';
                            if (container) {
                                const h3 = container.querySelector('h3');
                                title = h3 ? h3.textContent.trim() : link.textContent.trim();
                                const snippetEl = container.querySelector('.VwiC3b, [data-sncf], [data-snf]');
                                snippet = snippetEl ? snippetEl.textContent.trim() : '';
                            }
                            jobs.push({
                                title: title,
                                url: href.split('&')[0],
                                snippet: snippet,
                            });
                        }
                    });
                    return jobs;
                }""")

                for job in results:
                    url = job.get("url", "")
                    if not url or url in seen_urls:
                        continue
                    seen_urls.add(url)

                    # Parse title - remove " - Melbourne, VIC" suffix
                    title = job.get("title", "")
                    title = re.sub(r'\s*[-–]\s*Melbourne.*$', '', title, flags=re.IGNORECASE).strip()
                    # Remove "Company Name -" prefix
                    title = re.sub(r'^.*?\s*[-–]\s*', '', title).strip() if ' - ' in title else title

                    # Try to extract company from snippet
                    snippet = job.get("snippet", "")
                    company = ""
                    # Indeed snippets often have "Company Name · Location"
                    m = re.search(r'^([·\-–|])\s*(.+?)(?:\s*[·\-–|]|$)', snippet)
                    if m:
                        company = m.group(2).strip()
                    # Also try "in Company" pattern
                    if not company:
                        m = re.search(r'(?:at|in|for)\s+([A-Z][A-Za-z\s&]+)', snippet)
                        if m:
                            company = m.group(1).strip()

                    all_jobs.append({
                        "title": title,
                        "company": company,
                        "url": url,
                        "location": "Melbourne, VIC",
                        "posted": "",
                        "source": "Indeed",
                        "salary": "",
                        "description": snippet[:500],
                        "tags": [keyword.split()[0].lower(), "indeed"],
                        "why": f"Indeed listing for {title} at {company}" if company else f"Indeed listing for {title}",
                        "score": 0,
                        "listing_verification": "indeed_via_google",
                        "application_route": url,
                        "application_route_type": "indeed_direct",
                        "remote": "remote" in title.lower() or "remote" in snippet.lower(),
                    })
                    collected += 1
                    if collected >= MAX_PER_KEYWORD:
                        break

            except Exception as e:
                print(f"    Error: {e}")

            print(f"    -> {collected} jobs")
            time.sleep(2)

        browser.close()

    return all_jobs


def main():
    output_dir = Path(__file__).parent
    output_path = output_dir / "jobs_indeed_google.json"

    print("Scraping Indeed via Google search...")
    jobs = scrape_indeed_via_google()

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "source": "indeed_google",
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "count": len(jobs),
            "jobs": jobs,
        }, f, indent=2, ensure_ascii=False)

    print(f"\nIndeed (via Google): {len(jobs)} jobs -> {output_path.name}")
    return jobs


if __name__ == "__main__":
    main()
