#!/usr/bin/env python
"""
Task 4: Generate visualizations and print bank-specific insights.

Usage:
    python scripts/generate_insights.py
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import ANALYZED_REVIEWS_CSV, REPORTS_DIR
from src.thematic_analysis import performance_issue_share
from src.visualize import generate_all_plots

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def drivers_and_pain_points(df: pd.DataFrame) -> dict:
    """Extract satisfaction drivers and pain points per bank from data."""
    insights = {}
    for bank, group in df.groupby("bank"):
        positive = group[group["sentiment_label"] == "positive"]
        negative = group[
            (group["sentiment_label"] == "negative") | (group["rating"] <= 2)
        ]

        pos_themes = positive["identified_theme"].value_counts().head(2)
        neg_themes = negative["identified_theme"].value_counts().head(2)

        insights[bank] = {
            "mean_rating": round(group["rating"].mean(), 2),
            "positive_pct": round((group["sentiment_label"] == "positive").mean() * 100, 1),
            "satisfaction_drivers": pos_themes.to_dict(),
            "pain_points": neg_themes.to_dict(),
            "recommendations": _recommendations(bank, group, neg_themes.index.tolist()),
        }
    return insights


def _recommendations(bank: str, group: pd.DataFrame, top_pain_themes: list) -> list[str]:
    """Bank-specific product recommendations grounded in themes."""
    recs = []
    perf = performance_issue_share(group)
    if not perf.empty and perf.iloc[0]["performance_mention_pct"] > 10:
        recs.append(
            "Prioritize transfer and loading performance: optimize API latency and "
            "add in-app progress indicators during transactions."
        )
    theme_set = set(top_pain_themes)
    if "Account Access Issues" in theme_set:
        recs.append(
            "Strengthen login/OTP reliability and add self-service recovery; "
            "consider biometric login to reduce support tickets."
        )
    if "Stability & Crashes" in theme_set:
        recs.append("Invest in crash monitoring (Firebase/Crashlytics) and staged rollouts.")
    if "Feature Requests" in theme_set or len(recs) < 2:
        recs.append(
            "Ship high-demand features (budgeting, notifications, fingerprint login) "
            "identified in review keyword analysis."
        )
    return recs[:3]


def main() -> None:
    if not ANALYZED_REVIEWS_CSV.exists():
        logger.error("Run sentiment analysis first: %s missing", ANALYZED_REVIEWS_CSV)
        sys.exit(1)

    df = pd.read_csv(ANALYZED_REVIEWS_CSV)
    paths = generate_all_plots(df)
    logger.info("Generated %d plots", len(paths))

    insights = drivers_and_pain_points(df)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPORTS_DIR / "insights_summary.json"
    out_path.write_text(json.dumps(insights, indent=2), encoding="utf-8")

    for bank, data in insights.items():
        logger.info("\n=== %s ===", bank)
        logger.info("Rating: %s | Positive sentiment: %s%%", data["mean_rating"], data["positive_pct"])
        logger.info("Drivers: %s", data["satisfaction_drivers"])
        logger.info("Pain points: %s", data["pain_points"])
        logger.info("Recommendations: %s", data["recommendations"])

    logger.info("Insights saved to %s", out_path)


if __name__ == "__main__":
    main()
