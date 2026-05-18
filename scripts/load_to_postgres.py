#!/usr/bin/env python
"""
Task 3: Apply schema and load analyzed reviews into PostgreSQL.

Prerequisites:
    createdb bank_reviews   (or via pgAdmin)
    Set POSTGRES_* env vars or use defaults in .env.example

Usage:
    python scripts/load_to_postgres.py
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

from src.database import load_reviews_from_csv, run_schema, run_verification_queries

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    try:
        run_schema()
        count = load_reviews_from_csv()
        results = run_verification_queries()
        logger.info("Loaded %d reviews", count)
        logger.info("Verification:\n%s", json.dumps(results, indent=2, default=str))
    except Exception as exc:
        logger.error(
            "Database load failed: %s. Ensure PostgreSQL is running and bank_reviews exists.",
            exc,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
