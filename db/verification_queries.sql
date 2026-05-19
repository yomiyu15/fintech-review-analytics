-- Task 3: data integrity verification queries
-- Run after load: psql -U postgres -d bank_reviews -f db/verification_queries.sql

-- 1. Review count per bank
SELECT b.bank_name, COUNT(r.review_id) AS review_count
FROM banks b
LEFT JOIN reviews r ON r.bank_id = b.bank_id
GROUP BY b.bank_id, b.bank_name
ORDER BY b.bank_id;

-- 2. Average rating per bank
SELECT b.bank_name,
       ROUND(AVG(r.rating)::numeric, 2) AS avg_rating,
       MIN(r.rating) AS min_rating,
       MAX(r.rating) AS max_rating
FROM banks b
JOIN reviews r ON r.bank_id = b.bank_id
GROUP BY b.bank_id, b.bank_name
ORDER BY b.bank_id;

-- 3. Null checks on key columns
SELECT
    COUNT(*) FILTER (WHERE review_text IS NULL)       AS null_review_text,
    COUNT(*) FILTER (WHERE rating IS NULL)            AS null_rating,
    COUNT(*) FILTER (WHERE review_date IS NULL)       AS null_review_date,
    COUNT(*) FILTER (WHERE sentiment_label IS NULL)   AS null_sentiment_label,
    COUNT(*) FILTER (WHERE identified_theme IS NULL)  AS null_identified_theme,
    COUNT(*) FILTER (WHERE bank_id IS NULL)           AS null_bank_id
FROM reviews;

-- 4. Total reviews (KPI: > 1,000)
SELECT COUNT(*) AS total_reviews FROM reviews;

-- 5. Sentiment distribution
SELECT sentiment_label, COUNT(*) AS n
FROM reviews
GROUP BY sentiment_label
ORDER BY n DESC;

-- 6. Themes per bank (KPI: 3+ distinct themes)
SELECT b.bank_name, r.identified_theme, COUNT(*) AS n
FROM reviews r
JOIN banks b ON b.bank_id = r.bank_id
GROUP BY b.bank_name, r.identified_theme
ORDER BY b.bank_name, n DESC;
