"""Pytest fixtures for database setup."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.db.duckdb import init_db  # noqa: E402
from app.db.seeder import seed_static_data  # noqa: E402


@pytest.fixture()
def fresh_db(tmp_path, monkeypatch):
    """Provision a temporary DuckDB database for each test."""
    db_path = tmp_path / "tasktracker-test.duckdb"
    monkeypatch.setenv("TASKTRACKER_DB_PATH", str(db_path))
    init_db()
    seed_static_data()
    yield

