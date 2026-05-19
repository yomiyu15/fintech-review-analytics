# Customer Experience Analytics for Fintech Apps
## Interim Submission — Report

**Author:** Omega Consultancy  
**Date:** May 2026  
**Banks analyzed:** Commercial Bank of Ethiopia (CBE), Bank of Abyssinia (BOA), Dashen Bank  
**Data source:** Google Play Store reviews (Ethiopia, `lang=en`, `country=et`)

---

## 1. Introduction

This interim report documents progress on a four-task pipeline: data collection and cleaning, sentiment and thematic NLP analysis, PostgreSQL persistence, and business insights with visualizations. The goal is to quantify customer experience for three Ethiopian mobile banking apps and produce actionable product recommendations.

**Dataset summary:** 1,277 cleaned reviews | May 2025 – May 2026 | 412–433 reviews per bank

---

## 2. Task 1 — Data Collection & Preprocessing

### Methodology
- Scraped via `google-play-scraper` with pagination (200 reviews/batch, NEWEST + MOST_RELEVANT sorts).
- Preprocessing: deduplication, null removal, date normalization, rating validation (1–5).

### Results

| Metric | Result |
|--------|--------|
| Raw reviews scraped | 1,305 |
| Clean reviews | **1,277** |
| Data loss | **2.15%** (< 5% KPI) |
| Date range | 2025-05-06 → 2026-05-17 |

| Bank | Clean reviews |
|------|---------------|
| Commercial Bank of Ethiopia | 412 |
| Bank of Abyssinia | 432 |
| Dashen Bank | 433 |

**Output:** `data/processed/reviews_clean.csv`

---

## 3. Task 2 — Sentiment & Thematic Analysis

### Sentiment
- **Model:** `distilbert-base-uncased-finetuned-sst-2-english` (DistilBERT SST-2).
- **Labels:** positive, negative, neutral (probability band 0.45–0.55), plus `non_english` for Amharic/mixed text.
- **Rationale:** Transformer outperforms lexicon tools (VADER/TextBlob) on short informal English; no reliable Amharic sentiment model — English-only scoring is intentional.
- **Coverage:** 91% of all reviews scored (1,162 English of 1,277).

### Thematic analysis
- TF-IDF keywords (unigrams + bigrams) per bank.
- Rule-based mapping to six business themes: Account Access, Transaction Performance, UI & Design, Customer Support, Feature Requests, Stability & Crashes.
- Themes applied to **all** reviews (including Amharic).

**Output:** `reviews_analyzed.csv`, `reviews_sentiment_export.csv`, `sentiment_summary.json`, `theme_summary.json`

---

## 4. Task 3 — PostgreSQL Storage

### Schema
- **`banks`:** `bank_id`, `bank_name`, `app_name`
- **`reviews`:** `review_id`, `bank_id` (FK), `review_text`, `rating`, `review_date`, `sentiment_label`, `sentiment_score`, `identified_theme`, `source`

### Load results
| KPI | Result |
|-----|--------|
| Total reviews in DB | **1,277** |
| Nulls in key columns | **0** |
| Banks seeded | 3 |

**Artifacts:** `db/schema.sql`, `scripts/load_to_postgres.py`

---

## 5. Task 4 — Insights & Recommendations

### Cross-bank comparison

| Bank | Reviews | Avg rating | % Positive | % Negative | Dominant theme |
|------|---------|------------|------------|------------|----------------|
| CBE | 412 | 4.10 | 61.7% | 27.4% | Transaction Performance |
| BOA | 432 | 3.63 | 51.6% | 38.7% | Transaction Performance |
| Dashen | 433 | 3.98 | 63.7% | 29.1% | UI & Design |

![Sentiment by bank](figures/01_sentiment_by_bank.png)

![Rating distribution](figures/02_rating_boxplot.png)

![Theme frequency](figures/03_theme_frequency.png)

![Sentiment trend](figures/04_sentiment_trend.png)

![Average rating](figures/05_avg_rating.png)

### CBE — Key findings
**Drivers:** Intuitive UI (15 positive UI reviews); customer support (11); speed/reliability (20 keyword matches).  
**Pain points:** Slow/failed transactions (25 negative); crashes (10).  
**Recommendations:** Payment status tracking (P1); stability sprint (P1); protect UI strengths (P2).

### BOA — Key findings
**Drivers:** Customer support (10); UI simplicity (5); speed keywords (12).  
**Pain points:** **Crashes (25 negative)** — highest among banks; failed transfers (24); OTP/login (9).  
**Recommendations:** Device compatibility testing & Crashlytics (P1); OTP/login redesign (P1); transfer performance (P1).

### Dashen — Key findings
**Drivers:** **UI & Design (40 positive)** — strongest UI signal; speed/reliability (39); support (8).  
**Pain points:** Transaction failures (23); login delays (8); post-update UX clutter.  
**Recommendations:** Transfer reliability (P1); streamline home screen (P2); OTP flow (P1).

---

## 6. Ethics & Limitations

- **Negativity bias:** Users often review after bad experiences.
- **English-only sentiment:** ~9–10% of reviews per bank are `non_english`; Amharic feedback is underrepresented in sentiment scores.
- **Scrape window:** ~1 year of history; may not reflect long-term trends.
- **Keyword themes:** Rule-based assignment can miss sarcasm and context.

---

## 7. Repository & Reproducibility

| Task | Script |
|------|--------|
| 1 | `scripts/scrape_and_preprocess.py` |
| 2 | `scripts/run_sentiment_analysis.py` |
| 3 | `scripts/load_to_postgres.py` |
| 4 | `scripts/generate_insights_report.py` |

**GitHub:** `fintech-review-analytics` — branches `task-1` through `task-4`.

---

*End of interim submission report.*
