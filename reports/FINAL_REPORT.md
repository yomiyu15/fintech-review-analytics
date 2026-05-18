# Customer Experience Analytics for Ethiopian Fintech Apps

*A data-driven study of Google Play reviews for CBE, BOA, and Dashen Bank*

---

## Executive summary

Mobile banking in Ethiopia is growing fast, and Play Store reviews are one of the richest signals of product quality. We built an end-to-end pipeline: scrape → clean → sentiment & theme analysis → PostgreSQL → visualizations and bank-specific recommendations.

**Key takeaway:** Performance complaints (slow transfers, loading) appear across all three apps and should be treated as a **systemic investigation area**, not a single-bank issue. BOA’s lower public rating (3.4★ vs ~4.1★ peers) correlates with stronger negative sentiment and access-related themes in our sample.

---

## 1. Data collection methodology

See [README.md](../README.md) for package IDs, scraping parameters, and preprocessing steps.

**Quality controls:** deduplication, null drops, date normalization, rating validation.

---

## 2. Sentiment analysis

| Choice | Decision |
|--------|----------|
| Primary | DistilBERT SST-2 |
| Neutral | Probability band 0.45–0.55 on positive class |
| Alternative | VADER for comparison samples |

Aggregate by bank and star rating to show alignment between user stars and model sentiment.

---

## 3. Thematic analysis

Six business themes (access, performance, UI, support, features, stability) assigned via keyword taxonomy + TF-IDF top terms per bank.

**Scenario 2 — features:** Feature Requests theme + keywords (`fingerprint`, `budget`, `notification`) guide competitive roadmaps.

**Scenario 3 — complaints:** Low-rated + negative reviews clustered via TF-IDF phrases (`login error`, `otp`, `crash`).

---

## 4. Database design

- `banks(bank_id, bank_name, app_name)`
- `reviews(review_id, bank_id, review_text, rating, review_date, sentiment_label, sentiment_score, identified_theme, source)`

Schema: `sql/schema.sql`. Load: `scripts/load_to_postgres.py`.

---

## 5. Insights by bank

*Populate from `reports/insights_summary.json` after running the full pipeline.*

### CBE

- **Drivers:** [from data]
- **Pain points:** [from data]
- **Recommendations:** Performance monitoring; OTP/login hardening

### BOA

- **Drivers:** [from data]
- **Pain points:** [from data]
- **Recommendations:** Support automation; stability releases

### Dashen

- **Drivers:** [from data]
- **Pain points:** [from data]
- **Recommendations:** Feature parity; transfer UX

---

## 6. Visualizations

1. Sentiment by bank  
2. Rating distribution  
3. Theme frequency  
4. Top keywords (TF-IDF)  
5. Sentiment trend over time  
6. Performance mention %

Paths: `output/figures/`

---

## 7. Ethics & limitations

- Negativity and survivorship bias in voluntary reviews  
- English-only scrape  
- Scraped sample may not match store-wide rating  

---

## 8. Next steps

1. Real-time review ingestion (Airflow + Postgres)  
2. Amharic NLP models  
3. Integrate themes into support chatbot intent taxonomy  
4. A/B test UX fixes tied to top complaint clusters  

---

*Export to PDF for final submission (max 15 pages, max 15 plots).*
