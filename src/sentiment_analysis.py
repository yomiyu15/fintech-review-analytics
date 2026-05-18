"""
Sentiment classification using DistilBERT (SST-2) with optional VADER comparison.

Maps binary model output to positive / negative / neutral via confidence thresholds.
"""

from __future__ import annotations

import logging
import os
from typing import Callable

import pandas as pd

from src.config import (
    ANALYZED_REVIEWS_CSV,
    NEUTRAL_SCORE_HIGH,
    NEUTRAL_SCORE_LOW,
    SENTIMENT_MODEL,
)

logger = logging.getLogger(__name__)

_pipeline = None


def _get_transformer_pipeline():
    """Lazy-load Hugging Face sentiment pipeline."""
    global _pipeline
    if _pipeline is not None:
        return _pipeline
    if os.environ.get("SKIP_TRANSFORMER_TESTS") == "1":
        return None
    from transformers import pipeline

    _pipeline = pipeline(
        "sentiment-analysis",
        model=SENTIMENT_MODEL,
        truncation=True,
        max_length=512,
    )
    return _pipeline


def label_from_scores(positive_score: float) -> tuple[str, float]:
    """
    Convert positive-class probability to three-way label.

    Neutral band when score is near 0.5 (low model confidence either way).
    """
    if NEUTRAL_SCORE_LOW <= positive_score <= NEUTRAL_SCORE_HIGH:
        label = "neutral"
        confidence = 1.0 - abs(positive_score - 0.5) * 2
    elif positive_score > NEUTRAL_SCORE_HIGH:
        label = "positive"
        confidence = positive_score
    else:
        label = "negative"
        confidence = 1.0 - positive_score
    return label, round(float(confidence), 4)


def classify_review_transformer(text: str) -> tuple[str, float]:
    """Classify a single review with DistilBERT SST-2."""
    pipe = _get_transformer_pipeline()
    if pipe is None:
        return _classify_review_vader(text)

    if not text or not str(text).strip():
        return "neutral", 0.0

    result = pipe(str(text)[:512])[0]
    label_raw = result["label"].upper()
    score = float(result["score"])

    if label_raw == "POSITIVE":
        positive_prob = score
    else:
        positive_prob = 1.0 - score

    return label_from_scores(positive_prob)


def _classify_review_vader(text: str) -> tuple[str, float]:
    """Fallback lexicon-based sentiment (VADER)."""
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

    analyzer = SentimentIntensityAnalyzer()
    if not text or not str(text).strip():
        return "neutral", 0.0
    scores = analyzer.polarity_scores(str(text))
    compound = scores["compound"]
    if compound >= 0.05:
        return "positive", round(min(1.0, (compound + 1) / 2), 4)
    if compound <= -0.05:
        return "negative", round(min(1.0, (-compound + 1) / 2), 4)
    return "neutral", round(1.0 - abs(compound), 4)


def classify_reviews_batch(
    texts: list[str],
    classifier: Callable[[str], tuple[str, float]] | None = None,
    batch_log_every: int = 100,
) -> pd.DataFrame:
    """Classify a list of review texts; returns labels and scores."""
    classify = classifier or classify_review_transformer
    labels, scores = [], []

    for i, text in enumerate(texts):
        label, score = classify(text)
        labels.append(label)
        scores.append(score)
        if batch_log_every and (i + 1) % batch_log_every == 0:
            logger.info("Classified %d / %d reviews", i + 1, len(texts))

    return pd.DataFrame({"sentiment_label": labels, "sentiment_score": scores})


def aggregate_sentiment_by_bank(df: pd.DataFrame) -> pd.DataFrame:
    """Mean sentiment score and label counts per bank."""
    if "bank" not in df.columns:
        raise ValueError("DataFrame must include 'bank' column")

    summary = (
        df.groupby("bank")
        .agg(
            review_count=("sentiment_score", "count"),
            mean_sentiment_score=("sentiment_score", "mean"),
            mean_rating=("rating", "mean"),
        )
        .reset_index()
    )
    for label in ["positive", "negative", "neutral"]:
        counts = df.groupby("bank")["sentiment_label"].apply(lambda s: (s == label).sum())
        summary[f"{label}_count"] = summary["bank"].map(counts)

    return summary


def aggregate_sentiment_by_rating(df: pd.DataFrame) -> pd.DataFrame:
    """Mean sentiment score grouped by star rating."""
    return (
        df.groupby(["bank", "rating"])
        .agg(mean_sentiment=("sentiment_score", "mean"), count=("review_id", "count"))
        .reset_index()
    )


def compare_vader_sample(df: pd.DataFrame, sample_size: int = 200) -> pd.DataFrame:
    """Compare DistilBERT vs VADER on a random sample for documentation."""
    sample = df.sample(n=min(sample_size, len(df)), random_state=42)
    transformer = classify_reviews_batch(sample["review"].tolist())
    vader = classify_reviews_batch(
        sample["review"].tolist(), classifier=_classify_review_vader
    )
    comparison = sample[["review_id", "review", "rating"]].copy()
    comparison["transformer_label"] = transformer["sentiment_label"].values
    comparison["vader_label"] = vader["sentiment_label"].values
    comparison["agreement"] = (
        comparison["transformer_label"] == comparison["vader_label"]
    )
    logger.info(
        "VADER vs DistilBERT agreement: %.1f%%",
        comparison["agreement"].mean() * 100,
    )
    return comparison


def run_sentiment_on_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Add sentiment columns to review DataFrame."""
    sentiment = classify_reviews_batch(df["review"].tolist())
    out = df.copy()
    out["sentiment_label"] = sentiment["sentiment_label"]
    out["sentiment_score"] = sentiment["sentiment_score"]
    return out


def save_analyzed(df: pd.DataFrame, path=ANALYZED_REVIEWS_CSV):
    """Persist analyzed reviews."""
    from pathlib import Path

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.info("Saved analyzed reviews to %s", path)
