"""
Scrape Google Play Store reviews for Ethiopian bank mobile apps.

Uses google-play-scraper with pagination to reach MIN_REVIEWS_PER_BANK per app.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

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
    SOURCE_LABEL,
)
from src.io_utils import write_csv_rows

logger = logging.getLogger(__name__)

SCRAPE_METADATA_PATH = DATA_RAW_DIR / "scrape_metadata.json"


def _parse_review_date(raw: Any) -> str | None:
    """Normalize Play Store datetime to YYYY-MM-DD."""
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw.strftime("%Y-%m-%d")
    if isinstance(raw, str):
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00")).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None


def scrape_app_reviews(
    package_id: str,
    bank_key: str,
    app_name: str,
    bank_name: str,
    target_count: int = MIN_REVIEWS_PER_BANK,
) -> list[dict[str, Any]]:
    """
    Fetch reviews for one app, paginating until target_count or no more results.

    Sorts by NEWEST first, then falls back to MOST_RELEVANT if needed.
    """
    collected: list[dict[str, Any]] = []
    continuation_token = None
    sort_orders = [Sort.NEWEST, Sort.MOST_RELEVANT]

    for sort in sort_orders:
        if len(collected) >= target_count:
            break
        continuation_token = None
        while len(collected) < target_count:
            batch_size = min(SCRAPE_BATCH_SIZE, target_count - len(collected) + 50)
            try:
                batch, continuation_token = reviews(
                    package_id,
                    lang=SCRAPE_LANG,
                    country=SCRAPE_COUNTRY,
                    sort=sort,
                    count=batch_size,
                    continuation_token=continuation_token,
                )
            except NotFoundError:
                logger.error("App not found: %s (%s)", package_id, bank_key)
                return collected
            except Exception as exc:
                logger.warning("Scrape error for %s: %s", bank_key, exc)
                break

            if not batch:
                break

            for item in batch:
                if len(collected) >= target_count:
                    break
                collected.append(
                    {
                        "review": (item.get("content") or "").strip(),
                        "rating": item.get("score"),
                        "date": _parse_review_date(item.get("at")),
                        "bank": bank_name,
                        "app_name": app_name,
                        "source": SOURCE_LABEL,
                        "review_id_play": item.get("reviewId"),
                    }
                )

            if len(collected) >= target_count or continuation_token is None:
                break

    logger.info("%s: collected %d reviews (target %d)", bank_key, len(collected), target_count)
    return collected[:target_count] if len(collected) > target_count else collected


def scrape_all_banks() -> list[dict[str, Any]]:
    """Scrape reviews for all configured banks."""
    all_rows: list[dict[str, Any]] = []

    for bank_key, meta in BANK_APPS.items():
        rows = scrape_app_reviews(
            package_id=meta["package_id"],
            bank_key=bank_key,
            app_name=meta["app_name"],
            bank_name=meta["bank_name"],
            target_count=MIN_REVIEWS_PER_BANK,
        )
        for row in rows:
            row["bank_key"] = bank_key
        all_rows.extend(rows)

    dates = [r["date"] for r in all_rows if r.get("date")]
    if dates:
        logger.info("Date range: %s to %s", min(dates), max(dates))

    return all_rows


def save_raw_reviews(rows: list[dict[str, Any]], path: Path = RAW_REVIEWS_CSV) -> Path:
    """Persist raw scrape to CSV."""
    if not rows:
        raise ValueError("No reviews to save")
    fieldnames = list(rows[0].keys())
    return write_csv_rows(path, rows, fieldnames=fieldnames)


def save_scrape_metadata(rows: list[dict[str, Any]]) -> Path:
    """Write scrape run summary for README / report documentation."""
    per_bank: dict[str, int] = {}
    for row in rows:
        bank = row.get("bank", "unknown")
        per_bank[bank] = per_bank.get(bank, 0) + 1

    dates = sorted(r["date"] for r in rows if r.get("date"))
    metadata = {
        "scraped_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "lang": SCRAPE_LANG,
        "country": SCRAPE_COUNTRY,
        "sort_orders": ["NEWEST", "MOST_RELEVANT"],
        "target_per_bank": MIN_REVIEWS_PER_BANK,
        "total_reviews": len(rows),
        "reviews_per_bank": per_bank,
        "date_range": {"min": dates[0], "max": dates[-1]} if dates else None,
        "apps": {
            k: {"package_id": v["package_id"], "app_name": v["app_name"]}
            for k, v in BANK_APPS.items()
        },
    }
    SCRAPE_METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCRAPE_METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    logger.info("Scrape metadata saved to %s", SCRAPE_METADATA_PATH)
    return SCRAPE_METADATA_PATH


def run_scrape() -> list[dict[str, Any]]:
    """Entry point: scrape all banks and save raw CSV + metadata."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    rows = scrape_all_banks()
    if rows:
        save_raw_reviews(rows)
        save_scrape_metadata(rows)
    return rows
