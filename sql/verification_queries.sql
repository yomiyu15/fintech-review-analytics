-- Task 3 verification queries — run in pgAdmin Query Tool on bank_reviews

-- 1. Review count per bank
SELECT b.bank_name, COUNT(r.review_id) AS review_count
FROM banks b
LEFT JOIN reviews r ON b.bank_id = r.bank_id
GROUP BY b.bank_name
ORDER BY b.bank_name;

-- 2. Average rating per bank
SELECT b.bank_name, ROUND(AVG(r.rating)::numeric, 2) AS avg_rating
FROM banks b
JOIN reviews r ON b.bank_id = r.bank_id
GROUP BY b.bank_name
ORDER BY avg_rating DESC;

-- 3. Null check on key columns
SELECT COUNT(*) AS null_sentiment_count
FROM reviews
WHERE sentiment_label IS NULL OR sentiment_score IS NULL;

-- 4. Sentiment distribution per bank
SELECT b.bank_name, r.sentiment_label, COUNT(*) AS n
FROM reviews r
JOIN banks b ON r.bank_id = b.bank_id
GROUP BY b.bank_name, r.sentiment_label
ORDER BY b.bank_name, n DESC;

-- 5. Top themes per bank
SELECT b.bank_name, r.identified_theme, COUNT(*) AS n
FROM reviews r
JOIN banks b ON r.bank_id = b.bank_id
WHERE r.identified_theme IS NOT NULL
GROUP BY b.bank_name, r.identified_theme
ORDER BY b.bank_name, n DESC;
