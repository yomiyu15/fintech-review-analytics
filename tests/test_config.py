from src.config import BANK_APPS, MIN_REVIEWS_PER_BANK


def test_three_banks():
    assert len(BANK_APPS) == 3


def test_package_ids():
    for m in BANK_APPS.values():
        assert "." in m["package_id"]


def test_min_target():
    assert MIN_REVIEWS_PER_BANK >= 400
