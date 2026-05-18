"""Smoke tests for project configuration."""

from src.config import BANK_APPS, MIN_REVIEWS_PER_BANK, THEME_KEYWORDS


def test_three_banks_configured():
    assert len(BANK_APPS) == 3
    assert "CBE" in BANK_APPS
    assert "BOA" in BANK_APPS
    assert "Dashen" in BANK_APPS


def test_package_ids_present():
    for meta in BANK_APPS.values():
        assert "package_id" in meta
        assert "." in meta["package_id"]


def test_min_reviews_target():
    assert MIN_REVIEWS_PER_BANK >= 400


def test_theme_taxonomy():
    assert len(THEME_KEYWORDS) >= 5
