"""
PostgreSQL persistence for cleaned and analyzed reviews (Task 3).
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

from src.config import ANALYZED_REVIEWS_CSV, BANK_APPS, DB_NAME, PROJECT_ROOT

logger = logging.getLogger(__name__)

SCHEMA_SQL = PROJECT_ROOT / "db" / "schema.sql"

BANK_ID_BY_NAME = {
    info["bank_name"]: idx + 1 for idx, (_, info) in enumerate(BANK_APPS.items())
}

BANK_ROWS = [
    (BANK_ID_BY_NAME[info["bank_name"]], info["bank_name"], info["app_name"])
    for info in BANK_APPS.values()
]


def get_db_config() -> dict[str, Any]:
    """Connection settings from environment (see .env.example)."""
    return {
        "host": os.environ.get("PGHOST", "localhost"),
        "port": int(os.environ.get("PGPORT", "5432")),
        "dbname": os.environ.get("PGDATABASE", DB_NAME),
        "user": os.environ.get("PGUSER", "postgres"),
        "password": os.environ.get("PGPASSWORD", ""),
    }


def connect():
    """Open a psycopg2 connection using env config."""
    cfg = get_db_config()
    if not cfg["password"]:
        raise ValueError(
            "PGPASSWORD is not set. Copy .env.example to .env and set your password."
        )
    return psycopg2.connect(**cfg)


def apply_schema(conn) -> None:
    """Create tables and indexes from db/schema.sql."""
    sql = SCHEMA_SQL.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    logger.info("Schema applied from %s", SCHEMA_SQL)


def seed_banks(conn) -> None:
    """Insert or update bank metadata."""
    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO banks (bank_id, bank_name, app_name)
            VALUES %s
            ON CONFLICT (bank_id) DO UPDATE
            SET bank_name = EXCLUDED.bank_name,
                app_name = EXCLUDED.app_name
            """,
            BANK_ROWS,
        )
    conn.commit()
    logger.info("Seeded %d banks", len(BANK_ROWS))


def _prepare_review_rows(df: pd.DataFrame) -> list[tuple]:
    """Map analyzed CSV rows to reviews table tuples."""
    rows = []
    for _, row in df.iterrows():
        bank_name = str(row["bank"])
        bank_id = BANK_ID_BY_NAME.get(bank_name)
        if bank_id is None:
            raise ValueError(f"Unknown bank name: {bank_name!r}")

        score = row.get("sentiment_score")
        if pd.isna(score):
            score_val = None
        else:
            score_val = round(float(score), 4)

        rows.append(
            (
                int(row["review_id"]),
                bank_id,
                str(row["review"]).strip(),
                int(row["rating"]),
                str(row["date"]),
                str(row["sentiment_label"]),
                score_val,
                str(row["identified_theme"]),
                str(row.get("source", "Google Play")),
            )
        )
    return rows


def load_reviews(conn, csv_path: Path | None = None, truncate: bool = False) -> int:
    """
    Load reviews from analyzed CSV into PostgreSQL.

    Returns number of rows inserted.
    """
    path = csv_path or ANALYZED_REVIEWS_CSV
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run Task 1 scrape and Task 2 sentiment first."
        )

    df = pd.read_csv(path)
    required = {
        "review_id",
        "review",
        "rating",
        "date",
        "bank",
        "sentiment_label",
        "identified_theme",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing columns: {sorted(missing)}")

    if "source" not in df.columns:
        df["source"] = "Google Play"

    rows = _prepare_review_rows(df)

    with conn.cursor() as cur:
        if truncate:
            cur.execute("TRUNCATE TABLE reviews RESTART IDENTITY CASCADE")
        execute_values(
            cur,
            """
            INSERT INTO reviews (
                review_id, bank_id, review_text, rating, review_date,
                sentiment_label, sentiment_score, identified_theme, source
            ) VALUES %s
            ON CONFLICT (review_id) DO UPDATE SET
                bank_id = EXCLUDED.bank_id,
                review_text = EXCLUDED.review_text,
                rating = EXCLUDED.rating,
                review_date = EXCLUDED.review_date,
                sentiment_label = EXCLUDED.sentiment_label,
                sentiment_score = EXCLUDED.sentiment_score,
                identified_theme = EXCLUDED.identified_theme,
                source = EXCLUDED.source
            """,
            rows,
            page_size=500,
        )
    conn.commit()
    logger.info("Loaded %d reviews from %s", len(rows), path)
    return len(rows)


def run_verification(conn) -> dict[str, Any]:
    """Run integrity checks and return structured results."""
    results: dict[str, Any] = {}

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT b.bank_name, COUNT(r.review_id)
            FROM banks b
            LEFT JOIN reviews r ON r.bank_id = b.bank_id
            GROUP BY b.bank_id, b.bank_name
            ORDER BY b.bank_id
            """
        )
        results["reviews_per_bank"] = [
            {"bank_name": row[0], "review_count": row[1]} for row in cur.fetchall()
        ]

        cur.execute(
            """
            SELECT b.bank_name, ROUND(AVG(r.rating)::numeric, 2)
            FROM banks b
            JOIN reviews r ON r.bank_id = b.bank_id
            GROUP BY b.bank_id, b.bank_name
            ORDER BY b.bank_id
            """
        )
        results["avg_rating_per_bank"] = [
            {"bank_name": row[0], "avg_rating": float(row[1])} for row in cur.fetchall()
        ]

        cur.execute(
            """
            SELECT
                COUNT(*) FILTER (WHERE review_text IS NULL),
                COUNT(*) FILTER (WHERE rating IS NULL),
                COUNT(*) FILTER (WHERE review_date IS NULL),
                COUNT(*) FILTER (WHERE sentiment_label IS NULL),
                COUNT(*) FILTER (WHERE identified_theme IS NULL)
            FROM reviews
            """
        )
        nulls = cur.fetchone()
        results["null_counts"] = {
            "review_text": nulls[0],
            "rating": nulls[1],
            "review_date": nulls[2],
            "sentiment_label": nulls[3],
            "identified_theme": nulls[4],
        }

        cur.execute("SELECT COUNT(*) FROM reviews")
        results["total_reviews"] = cur.fetchone()[0]

        cur.execute(
            """
            SELECT b.bank_name, COUNT(DISTINCT r.identified_theme)
            FROM reviews r
            JOIN banks b ON b.bank_id = r.bank_id
            GROUP BY b.bank_name
            ORDER BY b.bank_name
            """
        )
        results["distinct_themes_per_bank"] = [
            {"bank_name": row[0], "distinct_themes": row[1]} for row in cur.fetchall()
        ]

    return results
