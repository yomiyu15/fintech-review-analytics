from src.language_filter import is_english_for_sentiment


def test_english_review():
    assert is_english_for_sentiment("The app is slow during transfers")


def test_amharic_review():
    assert not is_english_for_sentiment("በጣም ቀላል ነው")


def test_mixed_with_ethiopic():
    assert not is_english_for_sentiment("features በጣም good")
