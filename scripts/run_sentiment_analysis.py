#!/usr/bin/env python
"""
Task 2: Sentiment (DistilBERT, English only) + thematic analysis (TF-IDF + themes).

Usage:
    python scripts/run_sentiment_analysis.py
    python scripts/run_sentiment_analysis.py --compare-vader
    python scripts/run_sentiment_analysis.py --sample 100
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import (
    ANALYZED_REVIEWS_CSV,
    CLEAN_REVIEWS_CSV,
    DATA_PROCESSED_DIR,
    SENTIMENT_EXPORT_CSV,
    SENTIMENT_SUMMARY_JSON,
    THEME_SUMMARY_JSON,
)
from src.sentiment_analysis import (
    aggregate_by_bank,
    aggregate_by_rating,
    add_sentiment_columns,
    compare_vader_sample,
    sentiment_labeled_pct,
)
from src.thematic_analysis import add_theme_column, themes_per_bank_summary

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def load_clean_reviews() -> pd.DataFrame:
    df = pd.read_csv(CLEAN_REVIEWS_CSV)
    if "review_id" not in df.columns:
        df.insert(0, "review_id", range(1, len(df) + 1))
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 2 sentiment + themes")
    parser.add_argument("--sample", type=int, default=0, help="Limit rows for quick test")
    parser.add_argument("--compare-vader", action="store_true")
    args = parser.parse_args()

    df = load_clean_reviews()
    if args.sample > 0:
        df = df.head(args.sample)
        log.info("Sample mode: %d reviews", len(df))

    log.info("Running sentiment (English-only DistilBERT)...")
    df = add_sentiment_columns(df)

    labeled_pct = sentiment_labeled_pct(df)
    english_pct = round(df["is_english"].mean() * 100, 1) if "is_english" in df.columns else 0.0
    log.info(
        "Sentiment scored: %.1f%% of all reviews (%d English, %.1f%% of corpus)",
        labeled_pct,
        int(df["is_english"].sum()) if "is_english" in df.columns else 0,
        english_pct,
    )
    if labeled_pct < 90:
        log.warning(
            "Below 90%% KPI on total reviews (%.1f%%). "
            "Non-English reviews are labeled non_english by design — "
            "run on full data/processed/reviews_clean.csv, not a small --sample slice.",
            labeled_pct,
        )

    log.info("Running thematic analysis...")
    df = add_theme_column(df)

    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(ANALYZED_REVIEWS_CSV, index=False)

    export = df[
        ["review_id", "review", "sentiment_label", "sentiment_score", "identified_theme"]
    ].copy()
    export = export.rename(columns={"review": "review_text"})
    export.to_csv(SENTIMENT_EXPORT_CSV, index=False)

    bank_summary = aggregate_by_bank(df)
    rating_summary = aggregate_by_rating(df)
    theme_summary = themes_per_bank_summary(df)

    summary = {
        "total_reviews": len(df),
        "english_reviews": int(df["is_english"].sum()),
        "sentiment_labeled_pct": labeled_pct,
        "tool": "distilbert-base-uncased-finetuned-sst-2-english (English only)",
        "non_english_label": "non_english",
        "by_bank": bank_summary.to_dict(orient="records") if not bank_summary.empty else [],
        "by_rating": rating_summary.to_dict(orient="records") if not rating_summary.empty else [],
    }
    SENTIMENT_SUMMARY_JSON.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    THEME_SUMMARY_JSON.write_text(json.dumps(theme_summary, indent=2), encoding="utf-8")

    log.info("Saved %s", ANALYZED_REVIEWS_CSV)
    log.info("Saved %s", SENTIMENT_EXPORT_CSV)
    log.info("\nSentiment by bank:\n%s", bank_summary.to_string() if not bank_summary.empty else "n/a")
    for bank, info in theme_summary.items():
        log.info("%s: %d themes | top: %s", bank, info["distinct_themes"], list(info["theme_counts"].keys())[:4])

    if args.compare_vader:
        compare_vader_sample(df)


if __name__ == "__main__":
    main()
