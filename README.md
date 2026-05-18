# Fintech Review Analytics — Task 1

Omega Consultancy: scrape and preprocess Google Play reviews for **CBE**, **BOA**, and **Dashen Bank**.

## Quick start

```bash
pip install -r requirements.txt
python scripts/scrape_and_preprocess.py
```

**Output:** `data/processed/reviews_clean.csv` (gitignored)

## Scraping methodology

| Bank | Package ID |
|------|------------|
| Commercial Bank of Ethiopia | `com.combanketh.mobilebanking` |
| Bank of Abyssinia | `com.boa.boaMobileBanking` |
| Dashen Bank | `com.dashen.dashensuperapp` |

- **Tool:** [google-play-scraper](https://github.com/JoMingyu/google-play-scraper)
- **Locale:** `lang=en`, `country=et`
- **Sort:** NEWEST, then MOST_RELEVANT
- **Pagination:** `continuation_token`, 200 reviews per batch
- **Target:** 435 raw reviews per bank (buffer for deduplication)

## Preprocessing (`src/preprocess.py`)

1. Remove duplicates (review + bank + date)
2. Drop rows missing review text or rating
3. Normalize dates to `YYYY-MM-DD`
4. Validate ratings 1–5
5. Export: `review`, `rating`, `date`, `bank`, `source`

## Task 1 results (verified run)

| Metric | Result |
|--------|--------|
| Raw reviews scraped | 1,305 |
| Clean reviews | **1,277** |
| Data loss | **2.15%** (< 5% KPI) |
| Date range | **2025-05-06 → 2026-05-17** |
| Unit tests | **8/8 passed** |

| Bank | Clean reviews |
|------|---------------|
| Commercial Bank of Ethiopia | 412 |
| Bank of Abyssinia | 432 |
| Dashen Bank | 433 |

## Task 1 checklist

| Requirement | Status |
|-------------|--------|
| ≥400 reviews per bank | Done |
| <5% missing data | Done (2.15%) |
| Clean CSV columns | `review`, `rating`, `date`, `bank`, `source` |
| `.gitignore` excludes `data/`, `*.csv` | Yes |
| CI: `pip install -r requirements.txt` on push to `main` | `.github/workflows/unittests.yml` |
| Branch `task-1` + Conventional Commits | Commit pending (see below) |

## Limitations

- English scrape may miss Amharic reviews.
- Play Store caps historical depth; we use two sort orders to maximize yield.
- Duplicate overlap across sort orders is removed (~2%).

## Project structure

```
fintech-review-analytics/
├── data/raw/              # reviews_raw.csv, scrape_metadata.json
├── data/processed/        # reviews_clean.csv, data_quality_report.json
├── src/scrape_reviews.py
├── src/preprocess.py
├── scripts/scrape_and_preprocess.py
└── tests/
```

## Git

```bash
git checkout task-1
git add .
git commit -m "feat(scrape): update Task 1 pipeline"
git push -u origin task-1
```
