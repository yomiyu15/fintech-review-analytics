"""Tests for database row preparation (no live PostgreSQL required)."""

import pandas as pd

from src.database import BANK_ID_BY_NAME, _prepare_review_rows


def test_prepare_review_rows_maps_bank_id():
    df = pd.DataFrame(
        {
            "review_id": [1],
            "review": ["Great app"],
            "rating": [5],
            "date": ["2025-01-01"],
            "bank": ["Commercial Bank of Ethiopia"],
            "source": ["Google Play"],
            "sentiment_label": ["positive"],
            "sentiment_score": [0.95],
            "identified_theme": ["UI & Design"],
        }
    )
    rows = _prepare_review_rows(df)
    assert len(rows) == 1
    assert rows[0][1] == BANK_ID_BY_NAME["Commercial Bank of Ethiopia"]
    assert rows[0][6] == 0.95


def test_prepare_review_rows_null_sentiment_score():
    df = pd.DataFrame(
        {
            "review_id": [2],
            "review": ["አፕሊኬሽን"],
            "rating": [3],
            "date": ["2025-01-02"],
            "bank": ["Dashen Bank"],
            "source": ["Google Play"],
            "sentiment_label": ["non_english"],
            "sentiment_score": [float("nan")],
            "identified_theme": ["General Feedback"],
        }
    )
    rows = _prepare_review_rows(df)
    assert rows[0][6] is None
