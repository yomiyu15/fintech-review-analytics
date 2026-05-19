"""
Thematic analysis: TF-IDF keywords + rule-based business themes (all languages).
"""

from __future__ import annotations

import logging
import re
from collections import Counter

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from src.config import THEME_KEYWORDS
from src.text_processing import normalize_text, preprocess_for_tfidf

logger = logging.getLogger(__name__)


def assign_theme(text: str) -> str:
    """
    Map review to one business theme by keyword hits.

    Highest hit count wins; tie-break by theme order in THEME_KEYWORDS.
    """
    norm = normalize_text(text)
    best_theme = "General Feedback"
    best_hits = 0
    for theme, keywords in THEME_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in norm)
        if hits > best_hits:
            best_hits = hits
            best_theme = theme
    return best_theme


def add_theme_column(df: pd.DataFrame, text_col: str = "review") -> pd.DataFrame:
    out = df.copy()
    out["identified_theme"] = out[text_col].apply(assign_theme)
    return out


def top_keywords_per_bank(
    df: pd.DataFrame,
    text_col: str = "review",
    top_n: int = 15,
    bank_col: str = "bank",
) -> dict[str, list[tuple[str, float]]]:
    """TF-IDF top terms per bank (unigrams + bigrams)."""
    result: dict[str, list[tuple[str, float]]] = {}
    for bank, group in df.groupby(bank_col):
        corpus = [preprocess_for_tfidf(t) for t in group[text_col].astype(str)]
        corpus = [c for c in corpus if c.strip()]
        if len(corpus) < 3:
            result[bank] = []
            continue
        try:
            vec = TfidfVectorizer(max_features=3000, ngram_range=(1, 2), min_df=2)
            matrix = vec.fit_transform(corpus)
            scores = matrix.sum(axis=0).A1
            terms = vec.get_feature_names_out()
            ranked = sorted(zip(terms, scores), key=lambda x: x[1], reverse=True)
            result[bank] = [(t, float(s)) for t, s in ranked[:top_n]]
        except ValueError:
            result[bank] = []
    return result


def theme_counts_per_bank(df: pd.DataFrame) -> pd.DataFrame:
    """Count reviews per bank per theme."""
    return (
        df.groupby(["bank", "identified_theme"])
        .size()
        .reset_index(name="count")
        .sort_values(["bank", "count"], ascending=[True, False])
    )


def themes_per_bank_summary(df: pd.DataFrame) -> dict:
    """Distinct themes and example keywords per bank for reporting."""
    keywords = top_keywords_per_bank(df)
    counts = theme_counts_per_bank(df)
    summary = {}
    for bank in df["bank"].unique():
        bank_counts = counts[counts["bank"] == bank]
        distinct = bank_counts["identified_theme"].nunique()
        top_themes = bank_counts.head(5).set_index("identified_theme")["count"].to_dict()
        summary[bank] = {
            "distinct_themes": int(distinct),
            "theme_counts": top_themes,
            "top_keywords": [k for k, _ in keywords.get(bank, [])[:10]],
        }
    return summary
