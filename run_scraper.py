#!/usr/bin/env python
"""Convenience script to run the scraper from the project root."""

import sys

from src.scrapers.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
