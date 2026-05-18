"""
PostgreSQL schema setup and data loading for bank reviews.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from src.config import ANALYZED_REVIEWS_CSV, BANK_APPS, PROJECT_ROOT

logger = logging.getLogger(__name__)

SCHEMA_SQL = PROJECT_ROOT / "sql" / "schema.sql"
DEFAULT_DB = "bank_reviews"


def get_connection_url() -> str:
    """Build PostgreSQL URL from environment variables."""
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    database = os.getenv("POSTGRES_DB", DEFAULT_DB)
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"


def get_engine(url: str | None = None) -> Engine:
    return create_engine(url or get_connection_url())


def run_schema(engine: Engine | None = None, schema_path: Path = SCHEMA_SQL) -> None:
    """Execute schema.sql to create tables."""
    engine = engine or get_engine()
    sql = schema_path.read_text(encoding="utf-8")
    with engine.begin() as conn:
        for statement in _split_sql_statements(sql):
            if statement.strip():
                conn.execute(text(statement))
    logger.info("Schema applied from %s", schema_path)


def _split_sql_statements(sql: str) -> list[str]:
    """Split SQL file on semicolons, skipping comments-only blocks."""
    parts = []
    current = []
    for line in sql.splitlines():
        stripped = line.strip()
        if stripped.startswith("--") and not current:
            continue
        current.append(line)
        if stripped.endswith(";"):
            parts.append("\n".join(current))
            current = []
    if current:
        parts.append("\n".join(current))
    return parts


def seed_banks(engine: Engine | None = None) -> dict[str, int]:
    """Insert bank metadata; return bank_name -> bank_id map."""
    engine = engine or get_engine()
    bank_ids = {}

    with engine.begin() as conn:
        for key, meta in BANK_APPS.items():
            result = conn.execute(
                text(
                    """
                    INSERT INTO banks (bank_name, app_name)
                    VALUES (:bank_name, :app_name)
                    ON CONFLICT (bank_name) DO UPDATE SET app_name = EXCLUDED.app_name
                    RETURNING bank_id
                    """
                ),
                {"bank_name": meta["bank_name"], "app_name": meta["app_name"]},
            )
            bank_ids[meta["bank_name"]] = result.scalar()

    return bank_ids


def load_reviews_from_csv(
    csv_path: Path | str = ANALYZED_REVIEWS_CSV,
    engine: Engine | None = None,
) -> int:
    """Insert analyzed reviews into PostgreSQL."""
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Analyzed CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)
    engine = engine or get_engine()
    bank_ids = seed_banks(engine)

    required = [
        "review_id", "review", "rating", "date", "bank",
        "sentiment_label", "sentiment_score", "identified_theme", "source",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"CSV missing columns: {missing}")

    text_col = "review" if "review" in df.columns else "review_text"
    inserted = 0

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM reviews"))
        for _, row in df.iterrows():
            bank_id = bank_ids.get(row["bank"])
            if bank_id is None:
                logger.warning("Unknown bank: %s", row["bank"])
                continue
            conn.execute(
                text(
                    """
                    INSERT INTO reviews (
                        review_id, bank_id, review_text, rating, review_date,
                        sentiment_label, sentiment_score, identified_theme, source
                    ) VALUES (
                        :review_id, :bank_id, :review_text, :rating, :review_date,
                        :sentiment_label, :sentiment_score, :identified_theme, :source
                    )
                    ON CONFLICT (review_id) DO UPDATE SET
                        sentiment_label = EXCLUDED.sentiment_label,
                        sentiment_score = EXCLUDED.sentiment_score,
                        identified_theme = EXCLUDED.identified_theme
                    """
                ),
                {
                    "review_id": int(row["review_id"]),
                    "bank_id": bank_id,
                    "review_text": row[text_col] if text_col in row else row["review"],
                    "rating": int(row["rating"]),
                    "review_date": row["date"],
                    "sentiment_label": row["sentiment_label"],
                    "sentiment_score": float(row["sentiment_score"]),
                    "identified_theme": row["identified_theme"],
                    "source": row.get("source", "Google Play"),
                },
            )
            inserted += 1

    logger.info("Inserted %d reviews", inserted)
    return inserted


def run_verification_queries(engine: Engine | None = None) -> dict:
    """Run integrity checks and return results."""
    engine = engine or get_engine()
    results = {}

    queries = {
        "reviews_per_bank": """
            SELECT b.bank_name, COUNT(r.review_id) AS review_count
            FROM banks b
            LEFT JOIN reviews r ON b.bank_id = r.bank_id
            GROUP BY b.bank_name
            ORDER BY b.bank_name
        """,
        "avg_rating_per_bank": """
            SELECT b.bank_name, ROUND(AVG(r.rating)::numeric, 2) AS avg_rating
            FROM banks b
            JOIN reviews r ON b.bank_id = r.bank_id
            GROUP BY b.bank_name
        """,
        "null_check": """
            SELECT COUNT(*) AS null_sentiment_count
            FROM reviews
            WHERE sentiment_label IS NULL OR sentiment_score IS NULL
        """,
    }

    with engine.connect() as conn:
        for name, sql in queries.items():
            rows = conn.execute(text(sql)).fetchall()
            results[name] = [dict(row._mapping) for row in rows]

    return results
