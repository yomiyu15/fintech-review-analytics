import pandas as pd

from src.insights import build_full_insights, extract_drivers_and_pains


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "review_id": range(1, 13),
            "review": [
                "Great UI very easy to use love it",
                "App crashes every day terrible",
                "Slow transfer failed again",
                "OTP never arrives cannot login",
                "Excellent support helped me fast",
                "Nice app works well",
                "Crash on startup bug",
                "Good UI design simple",
                "Payment pending slow",
                "Feature need budget tool",
                "Worst app hate crashes",
                "Fast reliable transfers",
            ],
            "rating": [5, 1, 2, 1, 5, 5, 1, 5, 2, 3, 1, 5],
            "date": ["2025-06-01"] * 12,
            "bank": ["Commercial Bank of Ethiopia"] * 6 + ["Bank of Abyssinia"] * 6,
            "source": ["Google Play"] * 12,
            "sentiment_label": [
                "positive", "negative", "negative", "negative", "positive", "positive",
                "negative", "positive", "negative", "neutral", "negative", "positive",
            ],
            "sentiment_score": [0.9, 0.8, 0.85, 0.9, 0.88, 0.7, 0.95, 0.8, 0.75, 0.5, 0.9, 0.85],
            "identified_theme": [
                "UI & Design", "Stability & Crashes", "Transaction Performance",
                "Account Access Issues", "Customer Support", "General Feedback",
                "Stability & Crashes", "UI & Design", "Transaction Performance",
                "Feature Requests", "Stability & Crashes", "Transaction Performance",
            ],
        }
    )


def test_extract_drivers_and_pains_minimum():
    df = _sample_df()
    result = extract_drivers_and_pains(df, "Commercial Bank of Ethiopia")
    assert len(result["drivers"]) >= 1
    assert len(result["pains"]) >= 1


def test_build_full_insights_structure():
    df = _sample_df()
    df["date"] = pd.to_datetime(df["date"])
    data = build_full_insights(df)
    assert "per_bank" in data
    assert "comparison" in data
    assert len(data["ethics_notes"]) >= 3
