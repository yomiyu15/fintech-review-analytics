"""Unit tests for preprocessing logic."""

import pandas as pd
import pytest

from src.preprocess import OUTPUT_COLS, preprocess_reviews


@pytest.fixture
def sample():
    return pd.DataFrame(
        {
            "review": ["Great app", "Great app", "", "Slow transfer"],
            "rating": [5, 5, 3, 2],
            "date": ["2024-01-15", "2024-01-15", "2024-02-01", None],
            "bank": ["Commercial Bank of Ethiopia"] * 4,
            "source": ["Google Play"] * 4,
        }
    )


def test_deduplication(sample):
    clean, report = preprocess_reviews(sample)
    assert report["duplicates_removed"] >= 1
    assert len(clean) < len(sample)


def test_drops_empty_review(sample):
    clean, report = preprocess_reviews(sample)
    assert report["dropped_missing_review"] >= 1


def test_output_columns(sample):
    clean, _ = preprocess_reviews(sample)
    assert list(clean.columns) == OUTPUT_COLS


def test_date_format(sample):
    clean, _ = preprocess_reviews(sample)
    assert clean["date"].str.match(r"\d{4}-\d{2}-\d{2}").all()


def test_rating_range(sample):
    clean, _ = preprocess_reviews(sample)
    assert clean["rating"].between(1, 5).all()
