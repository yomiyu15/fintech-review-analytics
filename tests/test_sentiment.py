import os

import pandas as pd

os.environ["SKIP_TRANSFORMER_TESTS"] = "1"

from src.sentiment_analysis import label_from_positive_prob, add_sentiment_columns


def test_neutral_band():
    label, score = label_from_positive_prob(0.5)
    assert label == "neutral"
    assert 0 <= score <= 1


def test_positive_label():
    label, _ = label_from_positive_prob(0.9)
    assert label == "positive"


def test_add_sentiment_columns_english():
    df = pd.DataFrame(
        {
            "review_id": [1, 2],
            "review": ["I love this app, excellent!", "Terrible crash hate it"],
            "rating": [5, 1],
            "bank": ["CBE", "CBE"],
            "date": ["2024-01-01", "2024-01-02"],
            "source": ["Google Play", "Google Play"],
        }
    )
    out = add_sentiment_columns(df)
    assert "sentiment_label" in out.columns
    assert out.loc[0, "sentiment_label"] in ("positive", "negative", "neutral")
