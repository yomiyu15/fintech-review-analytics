"""Central configuration for bank apps, paths, and analysis parameters."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
FIGURES_DIR = PROJECT_ROOT / "output" / "figures"
REPORTS_DIR = PROJECT_ROOT / "reports"

RAW_REVIEWS_CSV = DATA_RAW_DIR / "reviews_raw.csv"
CLEAN_REVIEWS_CSV = DATA_PROCESSED_DIR / "reviews_clean.csv"
ANALYZED_REVIEWS_CSV = DATA_PROCESSED_DIR / "reviews_analyzed.csv"

SOURCE_LABEL = "Google Play"
MIN_REVIEWS_PER_BANK = 435  # scrape extra to absorb duplicate removal (~5%)
SCRAPE_BATCH_SIZE = 200
SCRAPE_LANG = "en"
SCRAPE_COUNTRY = "us"

# Google Play package IDs and display names
BANK_APPS = {
    "CBE": {
        "bank_name": "Commercial Bank of Ethiopia",
        "app_name": "Commercial Bank of Ethiopia Mobile",
        "package_id": "com.combanketh.mobilebanking",
    },
    "BOA": {
        "bank_name": "Bank of Abyssinia",
        "app_name": "BoA Mobile",
        "package_id": "com.boa.boaMobileBanking",
    },
    "Dashen": {
        "bank_name": "Dashen Bank",
        "app_name": "Dashen Bank",
        "package_id": "com.dashen.dashensuperapp",
    },
}

# Theme taxonomy: keyword patterns mapped to business-relevant themes
THEME_KEYWORDS = {
    "Account Access Issues": [
        "login", "log in", "sign in", "password", "otp", "pin", "locked",
        "authentication", "verify", "verification", "fingerprint", "biometric",
    ],
    "Transaction Performance": [
        "slow", "loading", "transfer", "transaction", "payment", "delay",
        "pending", "failed", "timeout", "stuck", "processing",
    ],
    "UI & Design": [
        "ui", "interface", "design", "layout", "screen", "navigation",
        "easy", "simple", "user friendly", "look", "theme", "dark mode",
    ],
    "Customer Support": [
        "support", "service", "help", "call", "branch", "agent", "response",
        "complaint", "customer care", "helpline",
    ],
    "Feature Requests": [
        "feature", "add", "need", "wish", "budget", "loan", "statement",
        "notification", "alert", "update", "improve", "request",
    ],
    "Stability & Crashes": [
        "crash", "crashes", "freeze", "bug", "error", "glitch", "not working",
        "stopped", "force close", "unstable",
    ],
}

SENTIMENT_MODEL = "distilbert-base-uncased-finetuned-sst-2-english"
NEUTRAL_SCORE_LOW = 0.45
NEUTRAL_SCORE_HIGH = 0.55
