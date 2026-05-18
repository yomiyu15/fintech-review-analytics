#!/usr/bin/env python
"""
Generate synthetic review data when scraping is unavailable (offline dev / CI).

Produces ~450 rows per bank with realistic themes. NOT for production submission
unless scraping is documented as blocked — use scrape_and_preprocess.py first.
"""

from __future__ import annotations

import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import BANK_APPS, DATA_PROCESSED_DIR, DATA_RAW_DIR, SOURCE_LABEL

TEMPLATES = {
    "positive": [
        "Love the UI and fast navigation",
        "Transfers are quick and reliable",
        "Easy to check balance and pay bills",
        "Best mobile banking app in Ethiopia",
        "Fingerprint login works great",
    ],
    "negative": [
        "App crashes during transfer very frustrating",
        "OTP not received cannot login",
        "Slow loading when sending money",
        "Login error after update",
        "Transaction pending for hours",
    ],
    "neutral": [
        "Okay app could be better",
        "Works sometimes slow other times",
        "Average experience nothing special",
    ],
}


def _random_date(start: datetime, end: datetime) -> str:
    delta = end - start
    day = start + timedelta(days=random.randint(0, delta.days))
    return day.strftime("%Y-%m-%d")


def generate_bank_rows(bank_name: str, app_name: str, n: int = 450) -> list[dict]:
    rows = []
    end = datetime.utcnow()
    start = end - timedelta(days=900)
    for i in range(n):
        sentiment_pool = random.choices(
            ["positive", "negative", "neutral"], weights=[0.45, 0.4, 0.15]
        )[0]
        text = random.choice(TEMPLATES[sentiment_pool])
        rating = { "positive": random.choice([4, 5]), "negative": random.choice([1, 2]),
                   "neutral": random.choice([3, 4])}[sentiment_pool]
        rows.append(
            {
                "review": f"{text} #{i}",
                "rating": rating,
                "date": _random_date(start, end),
                "bank": bank_name,
                "app_name": app_name,
                "source": SOURCE_LABEL,
                "review_id_play": f"synthetic-{bank_name[:3]}-{i}",
            }
        )
    return rows


def main() -> None:
    random.seed(42)
    all_rows = []
    for meta in BANK_APPS.values():
        all_rows.extend(
            generate_bank_rows(meta["bank_name"], meta["app_name"], n=450)
        )

    df = pd.DataFrame(all_rows)
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    raw_path = DATA_RAW_DIR / "reviews_raw.csv"
    df.to_csv(raw_path, index=False)
    print(f"Wrote {len(df)} synthetic rows to {raw_path}")
    print("Run: python scripts/scrape_and_preprocess.py --skip-scrape")


if __name__ == "__main__":
    main()
