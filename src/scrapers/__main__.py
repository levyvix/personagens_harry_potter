"""Main entry point for the scraper package."""

import argparse
import asyncio

from .wiki_caller_async import WikiCaller as WikiCallerAsync
from .wiki_caller_multiprocessing import WikiCaller as WikiCallerMultiprocessing
from .wiki_caller_sync import WikiCaller as WikiCallerSync


def main():
    """Run the scraper with the specified mode."""
    parser = argparse.ArgumentParser(
        description=(
            "Harry Potter Wiki Scraper - Extract character data from "
            "Portuguese Harry Potter Wiki"
        )
    )
    parser.add_argument(
        "--mode",
        choices=["sync", "multiprocessing", "async"],
        default="multiprocessing",
        help=(
            "Scraping mode: sync (slower, BeautifulSoup), "
            "multiprocessing (fast, uses all cores), async (aiohttp)"
        ),
    )
    parser.add_argument(
        "--output-dir",
        default="data",
        help="Output directory for CSV and DuckDB files (default: data/)",
    )

    args = parser.parse_args()

    print(f"Output will be saved to: {args.output_dir}/")

    if args.mode == "sync":
        print("Running in synchronous mode (BeautifulSoup)...")
        scraper = WikiCallerSync()
        scraper.run()
    elif args.mode == "multiprocessing":
        print("Running in multiprocessing mode (uses all CPU cores)...")
        print("⚠️  WARNING: This may trigger rate limiting from the website.")
        scraper = WikiCallerMultiprocessing()
        scraper.run()
    else:  # async
        print("Running in async mode (aiohttp)...")
        scraper = WikiCallerAsync()
        asyncio.run(scraper.run())


if __name__ == "__main__":
    main()
