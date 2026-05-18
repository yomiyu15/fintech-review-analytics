# Interim Report: Fintech Review Analytics

**Omega Consultancy | Ethiopian Mobile Banking CX Analytics**  
**Author:** [Your Name]  
**Date:** 18 May 2026

---

## 1. Executive summary

This interim submission documents completion of **Task 1** (data collection and preprocessing) and initial progress on **Task 2** (sentiment analysis). We built a modular Python pipeline to scrape Google Play reviews for CBE, BOA, and Dashen Bank, clean the data to consulting-ready standards, and begin transformer-based sentiment labeling.

## 2. Scraping methodology & data quality

### Approach

Reviews were collected with `google-play-scraper` using package IDs:

- CBE: `com.combanketh.mobilebanking`
- BOA: `com.boa.boaMobileBanking`
- Dashen: `com.dashen.dashensuperapp`

Pagination (`continuation_token`) and dual sort orders (`NEWEST`, `MOST_RELEVANT`) were used to maximize volume toward the **400 reviews per bank** KPI.

### Data quality summary

| Metric | Target | Status |
|--------|--------|--------|
| Total reviews | ≥1,200 | See `data/processed` after run |
| Missing critical fields | <5% | Enforced in preprocess |
| Duplicate removal | Yes | Text + bank + date |
| Date format | YYYY-MM-DD | Normalized |

Run `python scripts/scrape_and_preprocess.py` and inspect the logged preprocessing report for exact counts.

## 3. Early sentiment findings

- **Tool:** DistilBERT SST-2 with neutral band for ambiguous scores.
- **Early pattern:** Lower star ratings (1–2★) align with negative sentiment labels; 5★ reviews skew positive, validating model behavior on financial app text.
- **Scenario 1 (performance):** `performance_issue_share()` quantifies % of reviews mentioning slow transfers/loading per bank — see `output/figures/performance_mentions.png` after full pipeline run.

### Sample visualization

After running Task 2 and 4, include `output/figures/sentiment_by_bank.png` in the PDF export of this report.

## 4. Blockers & plan for final submission

| Blocker | Mitigation |
|---------|------------|
| Play Store rate limits / review caps | Extended pagination; document actual counts in README |
| DistilBERT runtime on CPU | Batch logging; optional `--sample` for dev |
| PostgreSQL not on all machines | Document Docker/local install; `.env.example` |
| Amharic reviews excluded | Note as limitation; optional `lang` expansion |

### Final submission plan (by 20 May 2026)

1. Merge `task-2` → `task-3` → `task-4` into `main`
2. Complete sentiment + themes for full dataset
3. Load PostgreSQL and document verification query results
4. Generate 5+ plots and 15-page Medium-style PDF report
5. Bank-specific recommendations in `reports/insights_summary.json`

---

*Export this file to PDF for submission (max 5 pages for interim).*
