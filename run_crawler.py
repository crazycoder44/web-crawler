#!/usr/bin/env python3
"""
Entry point for running the web crawler.
Crawls books.toscrape.com and stores data in MongoDB.
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.crawler.runner import BooksCrawler
from src.crawler.logging_config import setup_logging


async def main():
    """Run the crawler."""
    # Setup logging
    setup_logging()
    
    # Create and run crawler
    crawler = BooksCrawler()
    await crawler.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Crawler interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Crawler failed: {e}")
        sys.exit(1)
