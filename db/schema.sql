-- Task 3: bank_reviews database schema
-- Run: psql -U postgres -d bank_reviews -f db/schema.sql

CREATE TABLE IF NOT EXISTS banks (
    bank_id   SMALLINT PRIMARY KEY,
    bank_name VARCHAR(120) NOT NULL UNIQUE,
    app_name  VARCHAR(160) NOT NULL
);

CREATE TABLE IF NOT EXISTS reviews (
    review_id        INTEGER PRIMARY KEY,
    bank_id          SMALLINT NOT NULL REFERENCES banks (bank_id) ON DELETE RESTRICT,
    review_text      TEXT NOT NULL,
    rating           SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    review_date      DATE NOT NULL,
    sentiment_label  VARCHAR(20) NOT NULL,
    sentiment_score  NUMERIC(6, 4),
    identified_theme VARCHAR(80) NOT NULL,
    source           VARCHAR(40) NOT NULL DEFAULT 'Google Play',
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT reviews_sentiment_score_range
        CHECK (sentiment_score IS NULL OR (sentiment_score >= 0 AND sentiment_score <= 1))
);

CREATE INDEX IF NOT EXISTS idx_reviews_bank_id ON reviews (bank_id);
CREATE INDEX IF NOT EXISTS idx_reviews_rating ON reviews (rating);
CREATE INDEX IF NOT EXISTS idx_reviews_review_date ON reviews (review_date);
CREATE INDEX IF NOT EXISTS idx_reviews_sentiment_label ON reviews (sentiment_label);

COMMENT ON TABLE banks IS 'Ethiopian retail bank metadata for Play Store apps';
COMMENT ON TABLE reviews IS 'Cleaned and NLP-enriched Play Store reviews';
