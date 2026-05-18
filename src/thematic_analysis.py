"""
Thematic analysis: TF-IDF keywords and rule-based theme assignment.
"""

from __future__ import annotations

import logging
import re
from collections import Counter

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from src.config import THEME_KEYWORDS

logger = logging.getLogger(__name__)

STOP_WORDS_EXTRA = {
    "app", "bank", "mobile", "use", "using", "used", "one", "get", "would",
    "also", "really", "much", "even", "still", "time", "day", "good", "bad",
}


def _normalize_text(text: str) -> str:
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9\s']", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def tokenize_for_tfidf(texts: list[str], use_spacy: bool = False) -> list[str]:
    """
    Join tokens for TF-IDF input. Optionally lemmatize with spaCy if available.
    """
    if use_spacy:
        try:
            import spacy

            nlp = spacy.load("en_core_web_sm", disable=["ner", "parser"])
            processed = []
            for doc in nlp.pipe(texts, batch_size=50):
                tokens = [
                    t.lemma_.lower()
                    for t in doc
                    if t.is_alpha and not t.is_stop and len(t) > 2
                ]
                processed.append(" ".join(tokens))
            return processed
        except OSError:
            logger.warning("spaCy model not found; using simple tokenization")

    processed = []
    for text in texts:
        tokens = [
            w
            for w in _normalize_text(text).split()
            if len(w) > 2 and w not in STOP_WORDS_EXTRA
        ]
        processed.append(" ".join(tokens))
    return processed


def extract_top_keywords(
    texts: list[str],
    top_n: int = 20,
    ngram_range: tuple[int, int] = (1, 2),
) -> list[tuple[str, float]]:
    """Return top TF-IDF terms (unigrams and bigrams)."""
    if not texts:
        return []

    corpus = tokenize_for_tfidf(texts)
    vectorizer = TfidfVectorizer(
        max_features=5000,
        ngram_range=ngram_range,
        min_df=2,
        stop_words="english",
    )
    try:
        matrix = vectorizer.fit_transform(corpus)
    except ValueError:
        return []

    scores = matrix.sum(axis=0).A1
    terms = vectorizer.get_feature_names_out()
    ranked = sorted(zip(terms, scores), key=lambda x: x[1], reverse=True)
    return ranked[:top_n]


def assign_theme(text: str) -> str:
    """
    Map review text to a business theme via keyword matching.

    Uses first matching theme by priority order in THEME_KEYWORDS.
    """
    normalized = _normalize_text(text)
    best_theme = "General Feedback"
    best_hits = 0

    for theme, keywords in THEME_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in normalized)
        if hits > best_hits:
            best_hits = hits
            best_theme = theme

    return best_theme


def assign_themes_to_dataframe(df: pd.DataFrame, text_col: str = "review") -> pd.DataFrame:
    """Add identified_theme column."""
    out = df.copy()
    out["identified_theme"] = out[text_col].apply(assign_theme)
    return out


def theme_summary_per_bank(df: pd.DataFrame) -> pd.DataFrame:
    """Count themes and top keywords per bank."""
    rows = []
    for bank, group in df.groupby("bank"):
        theme_counts = group["identified_theme"].value_counts().to_dict()
        keywords = extract_top_keywords(group["review"].tolist(), top_n=15)
        rows.append(
            {
                "bank": bank,
                "theme_counts": theme_counts,
                "top_keywords": [k for k, _ in keywords],
            }
        )
    return pd.DataFrame(rows)


def complaint_clusters(df: pd.DataFrame, min_rating: int = 2) -> pd.DataFrame:
    """
    Recurring complaints from low-rated reviews (Scenario 3).

    Returns phrase frequencies for negative-sentiment, low-star reviews.
    """
    subset = df[
        (df["rating"] <= min_rating)
        | (df.get("sentiment_label", pd.Series()) == "negative")
    ].copy()

    all_phrases: Counter = Counter()
    for bank, group in subset.groupby("bank"):
        keywords = extract_top_keywords(group["review"].tolist(), top_n=30)
        for phrase, weight in keywords:
            all_phrases[(bank, phrase)] += weight

    records = [
        {"bank": b, "phrase": p, "weight": w}
        for (b, p), w in all_phrases.most_common(50)
    ]
    return pd.DataFrame(records)


def performance_issue_share(df: pd.DataFrame) -> pd.DataFrame:
    """
    Scenario 1: share of reviews mentioning slow loading / transfers per bank.
    """
    perf_keywords = THEME_KEYWORDS["Transaction Performance"]
    rows = []
    for bank, group in df.groupby("bank"):
        mentions = group["review"].apply(
            lambda t: any(kw in _normalize_text(t) for kw in perf_keywords)
        )
        rows.append(
            {
                "bank": bank,
                "total_reviews": len(group),
                "performance_mentions": int(mentions.sum()),
                "performance_mention_pct": round(mentions.mean() * 100, 2),
                "mean_rating": round(group["rating"].mean(), 2),
            }
        )
    return pd.DataFrame(rows)
