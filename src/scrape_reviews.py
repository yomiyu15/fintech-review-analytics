"""
Scrape Google Play Store reviews for Ethiopian bank mobile apps.

Uses google-play-scraper with pagination (NEWEST, then MOST_RELEVANT).
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from typing import Any

import pandas as pd
from google_play_scraper import Sort, reviews
from google_play_scraper.exceptions import NotFoundError

from src.config import (
    BANK_APPS,
    DATA_RAW_DIR,
    MIN_REVIEWS_PER_BANK,
    RAW_REVIEWS_CSV,
    SCRAPE_BATCH_SIZE,
    SCRAPE_COUNTRY,
    SCRAPE_LANG,
    SCRAPE_METADATA_JSON,
    SOURCE_LABEL,
)

logger = logging.getLogger(__name__)


def _parse_date(raw: Any) -> str | None:
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw.strftime("%Y-%m-%d")
    try:
        return pd.to_datetime(raw).strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return None


def scrape_app_reviews(
    package_id: str,
    bank_key: str,
    bank_name: str,
    app_name: str,
    target: int = MIN_REVIEWS_PER_BANK,
) -> list[dict[str, Any]]:
    """Paginate until target reviews or no more pages."""
    collected: list[dict[str, Any]] = []
    sorts = [Sort.NEWEST, Sort.MOST_RELEVANT]

    for sort in sorts:
        if len(collected) >= target:
            break
        token = None
        while len(collected) < target:
            try:
                batch, token = reviews(
                    package_id,
                    lang=SCRAPE_LANG,
                    country=SCRAPE_COUNTRY,
                    sort=sort,
                    count=min(SCRAPE_BATCH_SIZE, target - len(collected) + 20),
                    continuation_token=token,
                )
            except NotFoundError:
                logger.error("App not found: %s", package_id)
                return collected
            except Exception as exc:
                logger.warning("%s scrape error: %s", bank_key, exc)
                break

            if not batch:
                break

            for item in batch:
                if len(collected) >= target:
                    break
                collected.append(
                    {
                        "review": (item.get("content") or "").strip(),
                        "rating": item.get("score"),
                        "date": _parse_date(item.get("at")),
                        "bank": bank_name,
                        "app_name": app_name,
                        "source": SOURCE_LABEL,
                        "review_id_play": item.get("reviewId"),
                    }
                )
            time.sleep(0.5)
            if token is None:
                break

    logger.info("%s: scraped %d (target %d)", bank_key, len(collected), target)
    return collected


def scrape_all_banks() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for key, meta in BANK_APPS.items():
        batch = scrape_app_reviews(
            meta["package_id"], key, meta["bank_name"], meta["app_name"]
        )
        rows.extend(batch)
    return pd.DataFrame(rows)


def save_raw(df: pd.DataFrame) -> None:
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(RAW_REVIEWS_CSV, index=False)

    per_bank = df.groupby("bank").size().to_dict() if not df.empty else {}
    dates = pd.to_datetime(df["date"], errors="coerce").dropna() if "date" in df else pd.Series()
    meta = {
        "scraped_at": datetime.utcnow().isoformat() + "Z",
        "lang": SCRAPE_LANG,
        "country": SCRAPE_COUNTRY,
        "sort_orders": ["NEWEST", "MOST_RELEVANT"],
        "target_per_bank": MIN_REVIEWS_PER_BANK,
        "total_reviews": len(df),
        "reviews_per_bank": per_bank,
        "date_range": {
            "min": str(dates.min().date()) if len(dates) else None,
            "max": str(dates.max().date()) if len(dates) else None,
        },
        "apps": {k: v["package_id"] for k, v in BANK_APPS.items()},
    }
    SCRAPE_METADATA_JSON.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    logger.info("Raw data: %s (%d rows)", RAW_REVIEWS_CSV, len(df))


def run_scrape() -> pd.DataFrame:
    df = scrape_all_banks()
    if not df.empty:
        save_raw(df)
    return df
