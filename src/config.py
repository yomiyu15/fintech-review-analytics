"""Project configuration for scraping, sentiment, and thematic analysis."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DOCS_DIR = PROJECT_ROOT / "docs"

RAW_REVIEWS_CSV = DATA_RAW_DIR / "reviews_raw.csv"
CLEAN_REVIEWS_CSV = DATA_PROCESSED_DIR / "reviews_clean.csv"
ANALYZED_REVIEWS_CSV = DATA_PROCESSED_DIR / "reviews_analyzed.csv"
SENTIMENT_EXPORT_CSV = DATA_PROCESSED_DIR / "reviews_sentiment_export.csv"
SENTIMENT_SUMMARY_JSON = DATA_PROCESSED_DIR / "sentiment_summary.json"
THEME_SUMMARY_JSON = DATA_PROCESSED_DIR / "theme_summary.json"
SCRAPE_METADATA_JSON = DATA_RAW_DIR / "scrape_metadata.json"
QUALITY_REPORT_JSON = DATA_PROCESSED_DIR / "data_quality_report.json"
THEME_GROUPING_MD = DOCS_DIR / "THEME_GROUPING.md"
DB_NAME = "bank_reviews"

# Task 4 — insights & report
REPORTS_DIR = PROJECT_ROOT / "reports"
REPORT_FIGURES_DIR = REPORTS_DIR / "figures"
INSIGHTS_REPORT_MD = REPORTS_DIR / "insights_report.md"
INSIGHTS_REPORT_PDF = REPORTS_DIR / "insights_report.pdf"
INSIGHTS_SUMMARY_JSON = REPORTS_DIR / "insights_summary.json"

BANK_SHORT_NAMES = {
    "Commercial Bank of Ethiopia": "CBE",
    "Bank of Abyssinia": "BOA",
    "Dashen Bank": "Dashen",
}

SOURCE_LABEL = "Google Play"
MIN_REVIEWS_PER_BANK = 435  # buffer so ≥400 remain after deduplication
SCRAPE_BATCH_SIZE = 200
SCRAPE_LANG = "en"
SCRAPE_COUNTRY = "et"  # Ethiopia

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

# --- Task 2: Sentiment (English-only for DistilBERT) ---
SENTIMENT_MODEL = "distilbert-base-uncased-finetuned-sst-2-english"
NEUTRAL_SCORE_LOW = 0.45
NEUTRAL_SCORE_HIGH = 0.55
NON_ENGLISH_SENTIMENT_LABEL = "non_english"

# Business themes: keywords matched in normalized review text (see docs/THEME_GROUPING.md)
THEME_KEYWORDS = {
    "Account Access Issues": [
        "login", "log in", "sign in", "password", "otp", "pin", "locked",
        "authentication", "verify", "verification", "fingerprint", "biometric",
    ],
    "Transaction Performance": [
        "slow", "loading", "transfer", "transaction", "payment", "delay",
        "pending", "failed", "timeout", "stuck", "processing", "lag",
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
