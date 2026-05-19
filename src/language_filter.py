"""Detect English reviews for transformer sentiment (Task 2)."""

from __future__ import annotations

import re

# Ethiopic script (Amharic, etc.)
ETHIOPIC_RE = re.compile(r"[\u1200-\u137F]")
# Mostly Latin letters, digits, common punctuation
LATIN_RATIO_MIN = 0.55


def is_english_for_sentiment(text: str, min_length: int = 4) -> bool:
    """
    Return True if review is suitable for English DistilBERT sentiment.

    Excludes text with Ethiopic characters or very low Latin letter ratio.
    Thematic analysis still runs on all reviews.
    """
    if not text or not str(text).strip():
        return False
    text = str(text).strip()
    if len(text) < min_length:
        return False
    if ETHIOPIC_RE.search(text):
        return False
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    latin = sum(1 for c in letters if ord(c) < 128)
    return (latin / len(letters)) >= LATIN_RATIO_MIN
