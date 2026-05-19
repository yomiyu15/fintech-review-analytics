"""
Sentiment analysis with DistilBERT (SST-2), English reviews only.

Non-English reviews get label non_english and no transformer score.
Optional VADER comparison on a sample for documentation.
"""

from __future__ import annotations

import logging
import os
from typing import Callable

import pandas as pd

from src.config import (
    NEUTRAL_SCORE_HIGH,
    NEUTRAL_SCORE_LOW,
    NON_ENGLISH_SENTIMENT_LABEL,
    SENTIMENT_MODEL,
)
from src.language_filter import is_english_for_sentiment

logger = logging.getLogger(__name__)

_pipeline = None


def _get_pipeline():
    global _pipeline
    if _pipeline is not None:
        return _pipeline
    if os.environ.get("SKIP_TRANSFORMER_TESTS") == "1":
        return None
    from transformers import pipeline

    logger.info("Loading sentiment model: %s", SENTIMENT_MODEL)
    _pipeline = pipeline(
        "sentiment-analysis",
        model=SENTIMENT_MODEL,
        truncation=True,
        max_length=512,
    )
    return _pipeline


def label_from_positive_prob(positive_prob: float) -> tuple[str, float]:
    """Map SST-2 positive probability to positive / negative / neutral + confidence."""
    if NEUTRAL_SCORE_LOW <= positive_prob <= NEUTRAL_SCORE_HIGH:
        return "neutral", round(1.0 - abs(positive_prob - 0.5) * 2, 4)
    if positive_prob > NEUTRAL_SCORE_HIGH:
        return "positive", round(positive_prob, 4)
    return "negative", round(1.0 - positive_prob, 4)


def classify_english_review(text: str) -> tuple[str, float]:
    """DistilBERT sentiment for a single English review."""
    pipe = _get_pipeline()
    if pipe is None:
        return _vader_fallback(text)

    result = pipe(str(text)[:512])[0]
    score = float(result["score"])
    label_raw = result["label"].upper()
    positive_prob = score if label_raw == "POSITIVE" else 1.0 - score
    return label_from_positive_prob(positive_prob)


def _vader_fallback(text: str) -> tuple[str, float]:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

    compound = SentimentIntensityAnalyzer().polarity_scores(str(text))["compound"]
    if compound >= 0.05:
        return "positive", round(min(1.0, (compound + 1) / 2), 4)
    if compound <= -0.05:
        return "negative", round(min(1.0, (-compound + 1) / 2), 4)
    return "neutral", round(1.0 - abs(compound), 4)


def add_sentiment_columns(df: pd.DataFrame, text_col: str = "review") -> pd.DataFrame:
    """
    Add sentiment_label and sentiment_score.

    English → DistilBERT. Non-English → non_english, NaN score.
    """
    out = df.copy()
    out["is_english"] = out[text_col].apply(is_english_for_sentiment)
    out["sentiment_label"] = NON_ENGLISH_SENTIMENT_LABEL
    out["sentiment_score"] = pd.NA

    english_mask = out["is_english"]
    n_english = int(english_mask.sum())
    logger.info("Sentiment (English only): %d / %d reviews", n_english, len(out))

    if n_english == 0:
        return out

    pipe = _get_pipeline()
    english_indices = out.index[english_mask].tolist()
    texts = [str(out.at[i, text_col])[:512] for i in english_indices]

    if pipe is None:
        for idx, text in zip(english_indices, texts):
            label, score = _vader_fallback(text)
            out.at[idx, "sentiment_label"] = label
            out.at[idx, "sentiment_score"] = score
        return out

    batch_size = 32
    for start in range(0, len(texts), batch_size):
        batch_texts = texts[start : start + batch_size]
        batch_idx = english_indices[start : start + batch_size]
        results = pipe(batch_texts)
        for idx, res in zip(batch_idx, results):
            score = float(res["score"])
            positive_prob = score if res["label"].upper() == "POSITIVE" else 1.0 - score
            label, conf = label_from_positive_prob(positive_prob)
            out.at[idx, "sentiment_label"] = label
            out.at[idx, "sentiment_score"] = conf
        done = min(start + batch_size, len(texts))
        if done % 200 < batch_size or done == len(texts):
            logger.info("Classified %d / %d English reviews", done, len(texts))

    return out


def sentiment_labeled_pct(df: pd.DataFrame) -> float:
    """Share of all reviews with DistilBERT sentiment (English + valid score)."""
    if df.empty:
        return 0.0
    valid = df.get("is_english", False) & df["sentiment_score"].notna()
    return round(valid.sum() / len(df) * 100, 2)


def aggregate_by_bank(df: pd.DataFrame) -> pd.DataFrame:
    """Mean sentiment score and label counts per bank (English scored rows)."""
    scored = df[df["sentiment_score"].notna()].copy()
    if scored.empty:
        return pd.DataFrame()
    summary = (
        scored.groupby("bank")
        .agg(
            n_scored=("sentiment_score", "count"),
            mean_sentiment_score=("sentiment_score", "mean"),
            mean_rating=("rating", "mean"),
        )
        .reset_index()
    )
    for label in ["positive", "negative", "neutral"]:
        counts = scored.groupby("bank")["sentiment_label"].apply(lambda s: (s == label).sum())
        summary[f"{label}_count"] = summary["bank"].map(counts)
    return summary


def aggregate_by_rating(df: pd.DataFrame) -> pd.DataFrame:
    """Mean sentiment by bank and star rating."""
    scored = df[df["sentiment_score"].notna()].copy()
    if scored.empty:
        return pd.DataFrame()
    return (
        scored.groupby(["bank", "rating"])
        .agg(mean_sentiment=("sentiment_score", "mean"), count=("review_id", "count"))
        .reset_index()
    )


def compare_vader_sample(df: pd.DataFrame, n: int = 150) -> pd.DataFrame:
    """Compare DistilBERT vs VADER on English sample."""
    english = df[df["is_english"]].head(n) if "is_english" in df.columns else df.head(n)
    rows = []
    for _, row in english.iterrows():
        text = row["review"]
        tr_label, _ = classify_english_review(text)
        va_label, _ = _vader_fallback(text)
        rows.append(
            {
                "review_id": row.get("review_id"),
                "transformer": tr_label,
                "vader": va_label,
                "agreement": tr_label == va_label,
            }
        )
    comp = pd.DataFrame(rows)
    logger.info("VADER agreement: %.1f%%", comp["agreement"].mean() * 100)
    return comp
