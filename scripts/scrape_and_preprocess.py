#!/usr/bin/env python
"""
Task 1: Scrape Google Play reviews and preprocess into a clean CSV.

Usage (from project root):
    python scripts/scrape_and_preprocess.py
    python scripts/scrape_and_preprocess.py --skip-scrape  # preprocess only
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.preprocess import run_preprocess
from src.scrape_reviews import run_scrape

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape and preprocess Play Store reviews")
    parser.add_argument(
        "--skip-scrape",
        action="store_true",
        help="Only run preprocessing on existing raw CSV",
    )
    args = parser.parse_args()

    if not args.skip_scrape:
        logger.info("Starting scrape for CBE, BOA, and Dashen...")
        raw_rows = run_scrape()
        logger.info("Scraped %d total reviews", len(raw_rows))

    clean_rows, report = run_preprocess()
    logger.info("Preprocessing complete: %s", report)
    logger.info("Clean CSV: data/processed/reviews_clean.csv")
    logger.info("Quality report: data/processed/data_quality_report.json")

    per_bank = report.get("reviews_per_bank", {})
    for bank, count in per_bank.items():
        status = "OK" if count >= 400 else "BELOW TARGET"
        logger.info("  %s: %d reviews [%s]", bank, count, status)

    total = report.get("final_count", 0)
    if total < 1200:
        logger.warning("Total %d reviews — below 1,200 target. See README limitations.", total)

    if report.get("missing_pct", 100) >= 5:
        logger.warning("Missing data %.1f%% exceeds 5%% KPI", report["missing_pct"])


if __name__ == "__main__":
    main()
