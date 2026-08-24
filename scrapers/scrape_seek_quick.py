#!/usr/bin/env python3
"""
Quick Seek scrape + merge + dashboard rebuild.
Run this to refresh Seek data and update the dashboard.

Usage:
    python3 scrape_seek_quick.py                    # Full scrape (all keywords)
    python3 scrape_seek_quick.py --keywords "IT support" "cloud engineer"  # Specific keywords
    python3 scrape_seek_quick.py --proxy socks5://127.0.0.1:1080  # With proxy
"""
import argparse
import sys
from pathlib import Path

SCRAPERS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRAPERS_DIR))

from seek_robust import scrape_seek
from merge_seek import merge_seek


def main():
    parser = argparse.ArgumentParser(description="Quick Seek scrape + merge + dashboard")
    parser.add_argument("--proxy", help="Proxy URL")
    parser.add_argument("--keywords", nargs="+", help="Override keywords")
    parser.add_argument("--max-per-keyword", type=int, default=25)
    parser.add_argument("--no-dashboard", action="store_true", help="Skip dashboard rebuild")
    args = parser.parse_args()

    # Scrape Seek
    print("=" * 60)
    print("SCRAPING SEEK")
    print("=" * 60)
    jobs = scrape_seek(
        proxy=args.proxy,
        keywords=args.keywords,
        max_per_keyword=args.max_per_keyword,
        strategies=["playwright"],
        enrich=False,
    )
    print(f"\nScraped {len(jobs)} Seek jobs")

    # Merge into combined
    print("\n" + "=" * 60)
    print("MERGING INTO COMBINED DATA")
    print("=" * 60)
    merge_seek()

    # Rebuild dashboard
    if not args.no_dashboard:
        print("\n" + "=" * 60)
        print("REBUILDING DASHBOARD")
        print("=" * 60)
        sys.path.insert(0, str(SCRAPERS_DIR.parent))
        from build_categorized_dashboard import build_dashboard
        build_dashboard(
            str(SCRAPERS_DIR / "jobs_combined.json"),
            str(SCRAPERS_DIR.parent / "index.html"),
        )
        print("Dashboard updated!")

    print("\n✅ Done!")


if __name__ == "__main__":
    main()
