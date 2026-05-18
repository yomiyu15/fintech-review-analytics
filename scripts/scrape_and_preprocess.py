#!/usr/bin/env python
"""Task 1 entry point: scrape Play Store reviews and preprocess."""

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.preprocess import run_preprocess
from src.scrape_reviews import run_scrape

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def main() -> None:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--skip-scrape", action="store_true")
    args = p.parse_args()

    if not args.skip_scrape:
        df = run_scrape()
        log.info("Scraped %d raw reviews", len(df))

    clean, report = run_preprocess()
    for bank, n in report.get("reviews_per_bank", {}).items():
        ok = "OK" if n >= 400 else "BELOW 400"
        log.info("  %s: %d [%s]", bank, n, ok)
    log.info("Total clean: %d | Data loss: %s%%", report["final_count"], report["missing_pct"])


if __name__ == "__main__":
    main()
