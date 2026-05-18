#!/usr/bin/env python
"""
Task 2: Sentiment and thematic analysis pipeline.

Usage:
    python scripts/run_sentiment_analysis.py
    python scripts/run_sentiment_analysis.py --sample 500  # faster dev run
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import ANALYZED_REVIEWS_CSV, CLEAN_REVIEWS_CSV, DATA_PROCESSED_DIR
from src.sentiment_analysis import (
    aggregate_sentiment_by_bank,
    aggregate_sentiment_by_rating,
    compare_vader_sample,
    run_sentiment_on_dataframe,
    save_analyzed,
)
from src.thematic_analysis import (
    assign_themes_to_dataframe,
    complaint_clusters,
    performance_issue_share,
    theme_summary_per_bank,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", type=int, default=0, help="Limit reviews for testing")
    parser.add_argument("--compare-vader", action="store_true", help="Run VADER comparison sample")
    args = parser.parse_args()

    clean_path = DATA_PROCESSED_DIR / "reviews_clean_with_id.csv"
    if not clean_path.exists():
        clean_path = CLEAN_REVIEWS_CSV
        df = pd.read_csv(clean_path)
        df.insert(0, "review_id", range(1, len(df) + 1))
    else:
        df = pd.read_csv(clean_path)

    if args.sample > 0:
        df = df.head(args.sample)
        logger.info("Using sample of %d reviews", len(df))

    logger.info("Running DistilBERT sentiment on %d reviews...", len(df))
    df = run_sentiment_on_dataframe(df)
    df = assign_themes_to_dataframe(df)

    save_analyzed(df)

    export_cols = [
        "review_id", "review", "sentiment_label", "sentiment_score", "identified_theme",
    ]
    export = df[export_cols].copy()
    export = export.rename(columns={"review": "review_text"})
    export_path = DATA_PROCESSED_DIR / "reviews_sentiment_export.csv"
    export.to_csv(export_path, index=False)

    logger.info("Bank sentiment summary:\n%s", aggregate_sentiment_by_bank(df).to_string())
    logger.info("Sentiment by rating:\n%s", aggregate_sentiment_by_rating(df).head(15).to_string())
    logger.info("Performance issues (Scenario 1):\n%s", performance_issue_share(df).to_string())
    logger.info("Complaint clusters sample:\n%s", complaint_clusters(df).head(10).to_string())

    if args.compare_vader:
        compare_vader_sample(df)

    themes = theme_summary_per_bank(df)
    for _, row in themes.iterrows():
        logger.info("%s themes: %s", row["bank"], row["theme_counts"])

    labeled_pct = df["sentiment_label"].notna().mean() * 100
    logger.info("Sentiment labeled: %.1f%%", labeled_pct)
    logger.info("Saved to %s", ANALYZED_REVIEWS_CSV)


if __name__ == "__main__":
    main()
