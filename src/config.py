"""Configuration for Task 1 — Play Store review scraping."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

RAW_REVIEWS_CSV = DATA_RAW_DIR / "reviews_raw.csv"
CLEAN_REVIEWS_CSV = DATA_PROCESSED_DIR / "reviews_clean.csv"
SCRAPE_METADATA_JSON = DATA_RAW_DIR / "scrape_metadata.json"
QUALITY_REPORT_JSON = DATA_PROCESSED_DIR / "data_quality_report.json"

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
