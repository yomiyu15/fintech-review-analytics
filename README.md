# Fintech Review Analytics

Customer experience analytics for **Commercial Bank of Ethiopia (CBE)**, **Bank of Abyssinia (BOA)**, and **Dashen Bank** Google Play Store reviews.

## Task 1 checklist

| Requirement | Status |
|-------------|--------|
| Scrape ≥400 reviews per bank | Done (412 / 432 / 433 after cleaning) |
| Fields: review, rating, date, bank, source | Done |
| Remove duplicates & missing values | Done (2.15% removed) |
| Dates normalized to `YYYY-MM-DD` | Done |
| `reviews_clean.csv` (gitignored) | `data/processed/reviews_clean.csv` |
| Preprocessing script with documentation | `src/preprocess.py` |
| Scraping script | `src/scrape_reviews.py` |
| README methodology & limitations | Below |
| `.gitignore` excludes `data/`, `*.csv` | Done |
| CI runs on push | `.github/workflows/unittests.yml` |
| Branch `task-1` with conventional commit | Done |

## Task 1 — Data collection & preprocessing (complete)

### Run Task 1

```powershell
cd d:\fintech-review-analytics
pip install -r requirements-task1.txt
python scripts/scrape_and_preprocess.py
```

Outputs (gitignored):

| File | Description |
|------|-------------|
| `data/raw/reviews_raw.csv` | Raw scrape |
| `data/raw/scrape_metadata.json` | Methodology stats |
| `data/processed/reviews_clean.csv` | **Deliverable** — 5 columns |
| `data/processed/reviews_clean_with_id.csv` | Same + `review_id` for later tasks |
| `data/processed/data_quality_report.json` | Dedup / missing-value counts |

### Scraping methodology

| Bank | App | Package ID |
|------|-----|------------|
| CBE | Commercial Bank of Ethiopia Mobile | `com.combanketh.mobilebanking` |
| BOA | BoA Mobile | `com.boa.boaMobileBanking` |
| Dashen | Dashen Bank (Super App) | `com.dashen.dashensuperapp` |

- **Library:** [google-play-scraper](https://github.com/JoMingyu/google-play-scraper)
- **Locale:** `lang=en`, `country=us`
- **Sort:** `NEWEST`, then `MOST_RELEVANT` if more reviews needed
- **Pagination:** 200 reviews per request via `continuation_token`
- **Target:** 435 raw per bank (buffer for duplicate removal)

### Latest run results

| Metric | Value |
|--------|-------|
| Raw reviews scraped | 1,305 |
| Clean reviews (after dedup) | **1,277** |
| Data loss | **2.15%** (< 5% KPI) |
| Date range | 2025-05-06 → 2026-05-17 |

| Bank | Clean reviews |
|------|---------------|
| Commercial Bank of Ethiopia | 412 |
| Bank of Abyssinia | 432 |
| Dashen Bank | 433 |

### Preprocessing (`src/preprocess.py`)

1. Remove duplicates (same review text + bank + date; Play Store review ID if present)
2. Drop rows missing review text or rating
3. Normalize dates to `YYYY-MM-DD`
4. Validate ratings as integers 1–5
5. Export columns: `review`, `rating`, `date`, `bank`, `source`

### Limitations

- English-only scrape (`lang=en`) may miss Amharic reviews.
- Play Store may return overlapping reviews across sort orders; dedup removes ~2%.
- Store-wide star ratings (e.g. CBE 4.2★) reflect all users; this sample is recent English reviews.

---

## Later tasks (not required for Task 1)

| Task | Command |
|------|---------|
| 2 — Sentiment & themes | `pip install -r requirements.txt` then `python scripts/run_sentiment_analysis.py` |
| 3 — PostgreSQL | `python scripts/load_to_postgres.py` |
| 4 — Insights & plots | `python scripts/generate_insights.py` |

See `sql/schema.sql` for database setup in pgAdmin.

## Project structure

```
scripts/scrape_and_preprocess.py   # Task 1 entry point
src/scrape_reviews.py
src/preprocess.py
src/io_utils.py
tests/test_preprocess.py
requirements-task1.txt             # google-play-scraper only
requirements.txt                   # full pipeline
```

## CI

`.github/workflows/unittests.yml` runs `pytest` on push to `main`.

## Git branches (recommended)

```text
task-1  → scrape + preprocess (this task)
task-2  → sentiment analysis
task-3  → PostgreSQL
task-4  → visualizations + report
```

Use Conventional Commits, e.g. `feat(scrape): collect 1,277 Play Store reviews`.
