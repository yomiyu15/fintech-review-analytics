"""Unit tests for database helpers (no live DB required)."""

import os
from pathlib import Path

import pytest

os.environ["SKIP_DB_TESTS"] = "1"

from src.database import _split_sql_statements


def test_split_sql_statements():
    sql = """
    -- comment
    CREATE TABLE banks (id INT);
    CREATE TABLE reviews (id INT);
    """
    parts = _split_sql_statements(sql)
    assert len(parts) >= 2
    assert "CREATE TABLE banks" in parts[0]


def test_schema_file_exists():
    schema = Path(__file__).resolve().parents[1] / "sql" / "schema.sql"
    assert schema.exists()
    content = schema.read_text()
    assert "banks" in content.lower()
    assert "reviews" in content.lower()
