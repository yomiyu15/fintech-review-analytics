"""Unit tests for sentiment and thematic analysis."""

import os

import pandas as pd
import pytest

os.environ["SKIP_TRANSFORMER_TESTS"] = "1"

from src.sentiment_analysis import classify_review_transformer, label_from_scores
from src.thematic_analysis import assign_theme, extract_top_keywords


def test_label_from_scores_neutral():
    label, score = label_from_scores(0.5)
    assert label == "neutral"
    assert 0 <= score <= 1


def test_label_from_scores_positive():
    label, _ = label_from_scores(0.9)
    assert label == "positive"


def test_vader_positive():
    label, score = classify_review_transformer("I love this app, excellent service!")
    assert label == "positive"
    assert score > 0


def test_vader_negative():
    label, _ = classify_review_transformer("Terrible app, crashes constantly, hate it.")
    assert label == "negative"


def test_assign_theme_login():
    theme = assign_theme("Cannot login, OTP not received")
    assert theme == "Account Access Issues"


def test_assign_theme_slow_transfer():
    theme = assign_theme("Transfer is very slow and loading takes forever")
    assert theme == "Transaction Performance"


def test_tfidf_keywords():
    texts = [
        "slow transfer loading",
        "slow transfer again",
        "fast UI design",
        "login error otp",
    ] * 5
    keywords = extract_top_keywords(texts, top_n=5)
    assert len(keywords) > 0
    assert all(isinstance(k, tuple) and len(k) == 2 for k in keywords)


def test_sentiment_dataframe():
    df = pd.DataFrame({"review": ["great app", "awful crash", "okay"]})
    from src.sentiment_analysis import classify_reviews_batch

    result = classify_reviews_batch(df["review"].tolist())
    assert len(result) == 3
    assert set(result["sentiment_label"]) <= {"positive", "negative", "neutral"}
