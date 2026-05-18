"""Unit tests for review preprocessing."""

import pytest

from src.preprocess import preprocess_reviews, REQUIRED_OUTPUT_COLS

DATE_RE = __import__("re").compile(r"^\d{4}-\d{2}-\d{2}$")


@pytest.fixture
def sample_raw():
    return [
        {
            "review": "Great app for transfers",
            "rating": 5,
            "date": "2024-01-15",
            "bank": "Commercial Bank of Ethiopia",
            "source": "Google Play",
        },
        {
            "review": "Great app for transfers",
            "rating": 5,
            "date": "2024-01-15",
            "bank": "Commercial Bank of Ethiopia",
            "source": "Google Play",
        },
        {
            "review": "Slow loading during transfer",
            "rating": 2,
            "date": "2024-02-01",
            "bank": "Commercial Bank of Ethiopia",
            "source": "Google Play",
        },
        {
            "review": "",
            "rating": 4,
            "date": "2024-03-01",
            "bank": "Commercial Bank of Ethiopia",
            "source": "Google Play",
        },
        {
            "review": "OTP not received",
            "rating": 1,
            "date": None,
            "bank": "Commercial Bank of Ethiopia",
            "source": "Google Play",
        },
    ]


def test_deduplication(sample_raw):
    clean, report = preprocess_reviews(sample_raw)
    assert report["duplicates_removed"] >= 1
    assert len(clean) < len(sample_raw)


def test_drops_missing_review_and_rating(sample_raw):
    clean, report = preprocess_reviews(sample_raw)
    assert report["dropped_missing_review"] >= 1
    assert all(r["review"] for r in clean)


def test_output_columns(sample_raw):
    clean, _ = preprocess_reviews(sample_raw)
    for col in REQUIRED_OUTPUT_COLS:
        assert col in clean[0]


def test_date_format(sample_raw):
    clean, _ = preprocess_reviews(sample_raw)
    assert all(DATE_RE.match(r["date"]) for r in clean)


def test_rating_range(sample_raw):
    clean, _ = preprocess_reviews(sample_raw)
    assert all(1 <= r["rating"] <= 5 for r in clean)
