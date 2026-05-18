"""
Preprocess scraped reviews: deduplicate, drop nulls, normalize dates.

Output columns: review, rating, date, bank, source
"""

from __future__ import annotations

import json
import logging

import pandas as pd

from src.config import (
    CLEAN_REVIEWS_CSV,
    DATA_PROCESSED_DIR,
    QUALITY_REPORT_JSON,
    RAW_REVIEWS_CSV,
)

logger = logging.getLogger(__name__)

OUTPUT_COLS = ["review", "rating", "date", "bank", "source"]


def preprocess_reviews(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Return cleaned DataFrame and quality report."""
    initial = len(df)
    report: dict = {"initial_count": initial}

    # Standardize column names
    df = df.rename(columns={"content": "review", "score": "rating", "bank_name": "bank"})

    before = len(df)
    df = df.drop_duplicates(subset=["review", "bank", "date"], keep="first")
    report["duplicates_removed"] = before - len(df)

    if "review_id_play" in df.columns:
        b = len(df)
        df = df.drop_duplicates(subset=["review_id_play"], keep="first")
        report["id_duplicates_removed"] = b - len(df)

    missing_review = df["review"].isna() | (df["review"].astype(str).str.strip() == "")
    missing_rating = df["rating"].isna()
    report["dropped_missing_review"] = int(missing_review.sum())
    report["dropped_missing_rating"] = int(missing_rating.sum())
    df = df.loc[~missing_review & ~missing_rating].copy()

    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df = df.dropna(subset=["rating"])
    df["rating"] = df["rating"].astype(int).clip(1, 5)

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    report["dropped_invalid_date"] = int(df["date"].isna().sum())
    df = df.dropna(subset=["date"])
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    if "source" not in df.columns:
        df["source"] = "Google Play"
    df["source"] = df["source"].fillna("Google Play")

    clean = df[OUTPUT_COLS].copy()
    report["final_count"] = len(clean)
    report["missing_pct"] = round((initial - len(clean)) / initial * 100, 2) if initial else 0
    report["reviews_per_bank"] = clean.groupby("bank").size().to_dict()

    logger.info("Preprocess report: %s", report)
    return clean, report


def run_preprocess(raw_path=RAW_REVIEWS_CSV, out_path=CLEAN_REVIEWS_CSV) -> tuple[pd.DataFrame, dict]:
    df = pd.read_csv(raw_path)
    clean, report = preprocess_reviews(df)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    clean.to_csv(out_path, index=False)
    QUALITY_REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    logger.info("Saved %d rows to %s", len(clean), out_path)
    return clean, report
