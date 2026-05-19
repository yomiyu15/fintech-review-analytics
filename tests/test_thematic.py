import pandas as pd

from src.thematic_analysis import assign_theme, add_theme_column


def test_theme_login():
    assert assign_theme("Cannot login, OTP not received") == "Account Access Issues"


def test_theme_slow_transfer():
    assert assign_theme("Transfer is very slow and loading") == "Transaction Performance"


def test_add_theme_column():
    df = pd.DataFrame({"review": ["app crashes often", "love the ui"]})
    out = add_theme_column(df)
    assert "identified_theme" in out.columns
    assert out.iloc[0]["identified_theme"] == "Stability & Crashes"
