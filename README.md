# Fintech Review Analytics

Omega Consultancy: Play Store review analytics for **CBE**, **BOA**, and **Dashen Bank**.

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
├── data/processed/        # reviews_clean.csv, reviews_analyzed.csv
├── db/                    # schema.sql, verification_queries.sql
├── src/scrape_reviews.py
├── src/preprocess.py
├── src/database.py
├── scripts/scrape_and_preprocess.py
├── scripts/run_sentiment_analysis.py
├── scripts/load_to_postgres.py
└── tests/
```

---

## Task 2 — Sentiment & thematic analysis

### Quick start

```bash
pip install -r requirements.txt
python -m nltk.downloader punkt stopwords
python -m spacy download en_core_web_sm   # optional, for lemmatization
python scripts/run_sentiment_analysis.py
```

**Requires:** `data/processed/reviews_clean.csv` from Task 1.

### Outputs (gitignored)

| File | Description |
|------|-------------|
| `data/processed/reviews_sentiment_export.csv` | `review_id`, `review_text`, `sentiment_label`, `sentiment_score`, `identified_theme` |
| `data/processed/reviews_analyzed.csv` | Full table (+ bank, rating, date, `is_english`) |
| `data/processed/sentiment_summary.json` | Aggregates by bank and rating |
| `data/processed/theme_summary.json` | Themes + keywords per bank |
| `docs/THEME_GROUPING.md` | Theme taxonomy and grouping logic |

### Sentiment (English only)

- **Model:** `distilbert-base-uncased-finetuned-sst-2-english` (Hugging Face)
- **Why:** Strong on short informal English text vs. lexicon-only tools (VADER/TextBlob).
- **Neutral:** positive-class probability between 0.45–0.55.
- **Non-English reviews** (Amharic / Ethiopic script): label `non_english`, no transformer score; themes still assigned. There is no reliable Amharic sentiment model in this pipeline — English-only scoring is intentional.
- **90% KPI:** DistilBERT scores every English review; on the full Task 1 corpus (~1,277 reviews) about **91%** are English, so **~91%** of all rows receive a score. Use the full run (`python scripts/run_sentiment_analysis.py`), not `--sample`, when checking this KPI.
- **Optional:** `--compare-vader` for tool comparison sample.

### Themes

- TF-IDF keywords per bank + rule-based mapping to 6 business themes (see `docs/THEME_GROUPING.md`).
- Tokenization + stop words via NLTK; optional spaCy lemmatization.

### Tool selection rationale

| Tool | Role |
|------|------|
| DistilBERT SST-2 | Primary sentiment (English reviews) |
| VADER | Optional comparison (`--compare-vader`) |
| TF-IDF + keyword rules | Themes and keyword evidence |

### Task 2 checklist

| Requirement | Status |
|-------------|--------|
| DistilBERT positive / negative / neutral + confidence | `src/sentiment_analysis.py` |
| English-only sentiment; Amharic → `non_english` | `src/language_filter.py` |
| Aggregate by bank and star rating | `sentiment_summary.json` |
| TF-IDF + 3–6 themes per bank | `src/thematic_analysis.py`, `docs/THEME_GROUPING.md` |
| Export CSV (`review_id`, `review_text`, `sentiment_label`, `sentiment_score`, `identified_theme`) | `reviews_sentiment_export.csv` |
| Modular pipeline script | `scripts/run_sentiment_analysis.py` |
| ≥400 reviews with sentiment (English subset) | ~1,162 on full clean corpus |
| Branch `task-2` + PR to `main` | Commit & push when ready |

---

## Task 3 — PostgreSQL storage

### Prerequisites

1. Install [PostgreSQL](https://www.postgresql.org/download/) (15+).
2. Create database: `CREATE DATABASE bank_reviews;` (pgAdmin or `psql`).
3. Copy credentials: `copy .env.example .env` and set `PGPASSWORD`.

### Schema

| Table | Purpose |
|-------|---------|
| `banks` | `bank_id`, `bank_name`, `app_name` |
| `reviews` | `review_id`, `bank_id` (FK), `review_text`, `rating`, `review_date`, `sentiment_label`, `sentiment_score`, `identified_theme`, `source` |

DDL: [`db/schema.sql`](db/schema.sql)

### Load data

Requires `data/processed/reviews_analyzed.csv` from Tasks 1–2.

```bash
pip install -r requirements.txt
python scripts/load_to_postgres.py
```

Options: `--truncate` (reload), `--verify-only` (queries only).

### Verify (SQL)

```bash
psql -U postgres -d bank_reviews -f db/verification_queries.sql
```

Or use the Python verification report: `data/processed/db_verification.json`.

| Check | Query / output |
|-------|----------------|
| Reviews per bank | `reviews_per_bank` in verification JSON |
| Avg rating per bank | `avg_rating_per_bank` |
| Null key columns | `null_counts` (expect all 0) |
| Total rows KPI | `total_reviews` > 1,000 |

### Task 3 checklist

| Requirement | Status |
|-------------|--------|
| Database `bank_reviews` | User-created |
| `banks` + `reviews` tables | `db/schema.sql` |
| Python insert script | `scripts/load_to_postgres.py` |
| >1,000 reviews loaded | After full pipeline load |
| Schema in Git | `db/schema.sql` |
| Verification queries | `db/verification_queries.sql` |
| README setup docs | This section |
| Branch `task-3` + PR | Commit & push when ready |

## Git

```bash
git checkout task-3
git add .
git commit -m "feat(db): add PostgreSQL schema and load pipeline"
git push -u origin task-3
```
