"""
Stakeholder-ready visualizations for fintech review analytics.
"""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.config import ANALYZED_REVIEWS_CSV, FIGURES_DIR
from src.thematic_analysis import extract_top_keywords, performance_issue_share

logger = logging.getLogger(__name__)

sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams["figure.dpi"] = 120
plt.rcParams["font.size"] = 10


def _ensure_output_dir(path: Path = FIGURES_DIR) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def plot_sentiment_by_bank(df: pd.DataFrame, save_path: Path | None = None) -> Path:
    """Stacked bar chart of sentiment distribution per bank."""
    out_dir = _ensure_output_dir()
    save_path = save_path or out_dir / "sentiment_by_bank.png"

    counts = (
        df.groupby(["bank", "sentiment_label"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=["positive", "neutral", "negative"], fill_value=0)
    )

    fig, ax = plt.subplots(figsize=(10, 6))
    counts.plot(kind="bar", stacked=True, ax=ax, color=["#2ecc71", "#95a5a6", "#e74c3c"])
    ax.set_title("Sentiment Distribution by Bank")
    ax.set_xlabel("Bank")
    ax.set_ylabel("Number of Reviews")
    ax.legend(title="Sentiment", bbox_to_anchor=(1.02, 1))
    plt.xticks(rotation=15, ha="right")
    plt.tight_layout()
    fig.savefig(save_path, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved %s", save_path)
    return save_path


def plot_rating_distribution(df: pd.DataFrame, save_path: Path | None = None) -> Path:
    """Boxplot of star ratings per bank."""
    out_dir = _ensure_output_dir()
    save_path = save_path or out_dir / "rating_distribution.png"

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.boxplot(data=df, x="bank", y="rating", ax=ax, palette="Blues")
    sns.stripplot(
        data=df.sample(min(500, len(df)), random_state=42),
        x="bank",
        y="rating",
        ax=ax,
        color=".25",
        alpha=0.15,
        size=2,
    )
    ax.set_title("Star Rating Distribution by Bank")
    ax.set_xlabel("Bank")
    ax.set_ylabel("Star Rating (1–5)")
    plt.xticks(rotation=15, ha="right")
    plt.tight_layout()
    fig.savefig(save_path, bbox_inches="tight")
    plt.close(fig)
    return save_path


def plot_theme_frequency(df: pd.DataFrame, save_path: Path | None = None) -> Path:
    """Horizontal bar chart of top themes per bank (faceted)."""
    out_dir = _ensure_output_dir()
    save_path = save_path or out_dir / "theme_frequency.png"

    theme_counts = (
        df.groupby(["bank", "identified_theme"])
        .size()
        .reset_index(name="count")
    )
    banks = theme_counts["bank"].unique()
    n_banks = len(banks)
    fig, axes = plt.subplots(1, n_banks, figsize=(5 * n_banks, 6), sharey=True)
    if n_banks == 1:
        axes = [axes]

    for ax, bank in zip(axes, banks):
        subset = (
            theme_counts[theme_counts["bank"] == bank]
            .nlargest(8, "count")
            .sort_values("count")
        )
        ax.barh(subset["identified_theme"], subset["count"], color="#3498db")
        ax.set_title(bank[:30])
        ax.set_xlabel("Review Count")

    fig.suptitle("Top Identified Themes per Bank", fontsize=14, y=1.02)
    plt.tight_layout()
    fig.savefig(save_path, bbox_inches="tight")
    plt.close(fig)
    return save_path


def plot_keywords_per_bank(df: pd.DataFrame, save_path: Path | None = None) -> Path:
    """Top TF-IDF keywords per bank."""
    out_dir = _ensure_output_dir()
    save_path = save_path or out_dir / "top_keywords.png"

    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    for ax, (bank, group) in zip(axes, df.groupby("bank")):
        keywords = extract_top_keywords(group["review"].tolist(), top_n=10)
        if not keywords:
            continue
        terms, scores = zip(*keywords)
        ax.barh(list(terms)[::-1], list(scores)[::-1], color="#9b59b6")
        ax.set_title(bank[:25])
        ax.set_xlabel("TF-IDF Score")

    fig.suptitle("Top Keywords by Bank (TF-IDF)", fontsize=14)
    plt.tight_layout()
    fig.savefig(save_path, bbox_inches="tight")
    plt.close(fig)
    return save_path


def plot_sentiment_trend(df: pd.DataFrame, save_path: Path | None = None) -> Path:
    """Monthly mean sentiment score by bank."""
    out_dir = _ensure_output_dir()
    save_path = save_path or out_dir / "sentiment_trend.png"

    trend = df.copy()
    trend["month"] = pd.to_datetime(trend["date"]).dt.to_period("M").astype(str)
    monthly = (
        trend.groupby(["bank", "month"])["sentiment_score"]
        .mean()
        .reset_index()
    )

    fig, ax = plt.subplots(figsize=(12, 6))
    for bank, group in monthly.groupby("bank"):
        ax.plot(group["month"], group["sentiment_score"], marker="o", label=bank[:20])

    ax.set_title("Sentiment Trend Over Time (Monthly Mean)")
    ax.set_xlabel("Month")
    ax.set_ylabel("Mean Sentiment Score")
    ax.legend(title="Bank", bbox_to_anchor=(1.02, 1))
    plt.xticks(rotation=45, ha="right")
    n_months = monthly["month"].nunique()
    if n_months > 12:
        ax.set_xticks(ax.get_xticks()[:: max(1, n_months // 12)])
    plt.tight_layout()
    fig.savefig(save_path, bbox_inches="tight")
    plt.close(fig)
    return save_path


def plot_performance_mentions(df: pd.DataFrame, save_path: Path | None = None) -> Path:
    """Bar chart for Scenario 1: slow transfer / loading mentions."""
    out_dir = _ensure_output_dir()
    save_path = save_path or out_dir / "performance_mentions.png"

    perf = performance_issue_share(df)
    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(
        perf["bank"].str.replace("Commercial Bank of Ethiopia", "CBE", regex=False),
        perf["performance_mention_pct"],
        color="#e67e22",
    )
    ax.set_title("Reviews Mentioning Slow Transfers / Loading (%)")
    ax.set_ylabel("% of Reviews")
    ax.set_xlabel("Bank")
    for bar, val in zip(bars, perf["performance_mention_pct"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3, f"{val}%", ha="center")
    plt.xticks(rotation=15, ha="right")
    plt.tight_layout()
    fig.savefig(save_path, bbox_inches="tight")
    plt.close(fig)
    return save_path


def generate_all_plots(df: pd.DataFrame | None = None) -> list[Path]:
    """Generate full visualization suite."""
    if df is None:
        df = pd.read_csv(ANALYZED_REVIEWS_CSV)
    paths = [
        plot_sentiment_by_bank(df),
        plot_rating_distribution(df),
        plot_theme_frequency(df),
        plot_keywords_per_bank(df),
        plot_sentiment_trend(df),
        plot_performance_mentions(df),
    ]
    return paths
