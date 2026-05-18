"""
Clean and normalize scraped Play Store reviews.

Outputs CSV with columns: review, rating, date, bank, source.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from src.config import CLEAN_REVIEWS_CSV, DATA_PROCESSED_DIR, RAW_REVIEWS_CSV
from src.io_utils import read_csv_rows, write_csv_rows

logger = logging.getLogger(__name__)

REQUIRED_OUTPUT_COLS = ["review", "rating", "date", "bank", "source"]
QUALITY_REPORT_PATH = DATA_PROCESSED_DIR / "data_quality_report.json"


def _normalize_columns(row: dict[str, Any]) -> dict[str, Any]:
    """Map alternate column names to canonical fields."""
    mapping = {
        "content": "review",
        "text": "review",
        "score": "rating",
        "bank_name": "bank",
    }
    out = dict(row)
    for old, new in mapping.items():
        if old in out and new not in out:
            out[new] = out.pop(old)
    return out


def _parse_date(value: Any) -> str | None:
    if value is None or str(value).strip() == "":
        return None
    s = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y"):
        try:
            return datetime.strptime(s[:19], fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(s.replace("Z", "")).strftime("%Y-%m-%d")
    except ValueError:
        return None


def _parse_rating(value: Any) -> int | None:
    try:
        r = int(float(value))
        return max(1, min(5, r))
    except (TypeError, ValueError):
        return None


def preprocess_reviews(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict]:
    """
    Deduplicate, drop missing critical fields, normalize dates.

    Returns cleaned rows and a quality report dict.
    """
    initial_count = len(rows)
    report: dict[str, Any] = {"initial_count": initial_count}

    normalized = [_normalize_columns(r) for r in rows]

    # Deduplicate by review + bank + date
    seen_text: set[tuple[str, str, str]] = set()
    seen_ids: set[str] = set()
    deduped: list[dict[str, Any]] = []
    duplicates_removed = 0
    id_duplicates_removed = 0

    for row in normalized:
        key = (
            str(row.get("review", "")).strip(),
            str(row.get("bank", "")),
            str(row.get("date", "")),
        )
        play_id = str(row.get("review_id_play", ""))
        if key in seen_text:
            duplicates_removed += 1
            continue
        if play_id and play_id in seen_ids:
            id_duplicates_removed += 1
            continue
        seen_text.add(key)
        if play_id:
            seen_ids.add(play_id)
        deduped.append(row)

    report["duplicates_removed"] = duplicates_removed
    report["id_duplicates_removed"] = id_duplicates_removed

    cleaned: list[dict[str, Any]] = []
    dropped_missing_review = 0
    dropped_missing_rating = 0
    dropped_invalid_date = 0

    for row in deduped:
        review = str(row.get("review", "")).strip()
        if not review:
            dropped_missing_review += 1
            continue

        rating = _parse_rating(row.get("rating"))
        if rating is None:
            dropped_missing_rating += 1
            continue

        date = _parse_date(row.get("date"))
        if date is None:
            dropped_invalid_date += 1
            continue

        source = str(row.get("source") or "Google Play").strip() or "Google Play"
        cleaned.append(
            {
                "review": review,
                "rating": rating,
                "date": date,
                "bank": str(row.get("bank", "")).strip(),
                "source": source,
            }
        )

    report["dropped_missing_review"] = dropped_missing_review
    report["dropped_missing_rating"] = dropped_missing_rating
    report["dropped_invalid_date"] = dropped_invalid_date

    # Assign review_id
    for i, row in enumerate(cleaned, start=1):
        row["review_id"] = i

    report["final_count"] = len(cleaned)
    report["missing_pct"] = round(
        (initial_count - len(cleaned)) / initial_count * 100, 2
    ) if initial_count else 0.0

    per_bank: dict[str, int] = {}
    for row in cleaned:
        per_bank[row["bank"]] = per_bank.get(row["bank"], 0) + 1
    report["reviews_per_bank"] = per_bank

    logger.info("Preprocessing report: %s", report)
    return cleaned, report


def load_raw_reviews(path: Path | str = RAW_REVIEWS_CSV) -> list[dict[str, Any]]:
    """Load raw CSV from disk."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Raw reviews not found: {path}. Run scrape first.")
    return read_csv_rows(path)


def save_clean_reviews(
    rows: list[dict[str, Any]], path: Path | str = CLEAN_REVIEWS_CSV
) -> Path:
    """Save cleaned dataset (5 required columns + optional review_id file)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    export = [{k: r[k] for k in REQUIRED_OUTPUT_COLS} for r in rows]
    write_csv_rows(path, export, fieldnames=REQUIRED_OUTPUT_COLS)

    with_id_path = path.parent / "reviews_clean_with_id.csv"
    write_csv_rows(
        with_id_path,
        rows,
        fieldnames=["review_id"] + REQUIRED_OUTPUT_COLS,
    )
    logger.info("Saved %d clean reviews to %s", len(rows), path)
    return path


def save_quality_report(report: dict) -> Path:
    """Persist preprocessing stats for documentation."""
    QUALITY_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    QUALITY_REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return QUALITY_REPORT_PATH


def run_preprocess(
    raw_path: Path | str = RAW_REVIEWS_CSV,
    clean_path: Path | str = CLEAN_REVIEWS_CSV,
) -> tuple[list[dict[str, Any]], dict]:
    """Load raw data, preprocess, and save."""
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    raw = load_raw_reviews(raw_path)
    clean, report = preprocess_reviews(raw)
    save_clean_reviews(clean, clean_path)
    save_quality_report(report)
    return clean, report
