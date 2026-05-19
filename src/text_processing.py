"""
Text preprocessing for thematic analysis: tokenization, stop words, lemmatization.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

try:
    from nltk.corpus import stopwords as nltk_stopwords
    from nltk.tokenize import word_tokenize

    _NLTK = True
except ImportError:
    _NLTK = False

# Fallback English stop words if NLTK data not downloaded
_FALLBACK_STOPS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "of",
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "will", "would", "could", "should", "may", "might",
    "i", "you", "he", "she", "it", "we", "they", "my", "your", "this", "that",
    "with", "from", "as", "by", "not", "no", "so", "if", "app", "bank",
}


def _get_stop_words() -> set[str]:
    if _NLTK:
        try:
            return set(nltk_stopwords.words("english"))
        except LookupError:
            pass
    return _FALLBACK_STOPS


def normalize_text(text: str) -> str:
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9\s']", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def tokenize(text: str, remove_stops: bool = True) -> list[str]:
    """Tokenize and optionally remove stop words."""
    normalized = normalize_text(text)
    if not normalized:
        return []
    if _NLTK:
        try:
            tokens = word_tokenize(normalized)
        except LookupError:
            tokens = normalized.split()
    else:
        tokens = normalized.split()
    stops = _get_stop_words() if remove_stops else set()
    return [t for t in tokens if len(t) > 2 and t not in stops]


def lemmatize_tokens(tokens: list[str], use_spacy: bool = True) -> list[str]:
    """Lemmatize with spaCy if available; otherwise return tokens unchanged."""
    if not tokens or not use_spacy:
        return tokens
    try:
        import spacy

        nlp = spacy.load("en_core_web_sm", disable=["ner", "parser"])
        doc = nlp(" ".join(tokens))
        return [
            t.lemma_.lower()
            for t in doc
            if t.is_alpha and t.lemma_ != "-PRON-"
        ]
    except OSError:
        logger.debug("spaCy en_core_web_sm not installed; skipping lemmatization")
        return tokens


def preprocess_for_tfidf(text: str, lemmatize: bool = True) -> str:
    """Full pipeline: tokenize → stop words → optional lemmatize → string for TF-IDF."""
    tokens = tokenize(text, remove_stops=True)
    if lemmatize:
        tokens = lemmatize_tokens(tokens)
    return " ".join(tokens)
