#!/usr/bin/env python
"""
Task 3: Load analyzed reviews into PostgreSQL (bank_reviews).

Usage:
    copy .env.example .env   # set PGPASSWORD
    python scripts/load_to_postgres.py
    python scripts/load_to_postgres.py --verify-only
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

from src.config import DATA_PROCESSED_DIR
from src.database import apply_schema, connect, load_reviews, run_verification, seed_banks

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def main() -> None:
    load_dotenv(ROOT / ".env")

    parser = argparse.ArgumentParser(description="Load reviews into PostgreSQL")
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Run verification queries only (no schema/load)",
    )
    parser.add_argument(
        "--truncate",
        action="store_true",
        help="Clear reviews table before insert",
    )
    args = parser.parse_args()

    conn = connect()
    try:
        if args.verify_only:
            results = run_verification(conn)
        else:
            apply_schema(conn)
            seed_banks(conn)
            n = load_reviews(conn, truncate=args.truncate)
            log.info("Inserted/updated %d reviews", n)
            results = run_verification(conn)

        out_path = DATA_PROCESSED_DIR / "db_verification.json"
        DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

        log.info("Total reviews in DB: %d", results["total_reviews"])
        for row in results["reviews_per_bank"]:
            log.info("  %s: %d reviews", row["bank_name"], row["review_count"])
        for row in results["avg_rating_per_bank"]:
            log.info("  %s: avg rating %.2f", row["bank_name"], row["avg_rating"])
        log.info("Null key columns: %s", results["null_counts"])
        log.info("Saved verification report: %s", out_path)

        if results["total_reviews"] < 1000:
            log.warning("Below 1,000 review KPI (got %d)", results["total_reviews"])
        if any(v > 0 for v in results["null_counts"].values()):
            log.warning("Null values found in key columns")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
