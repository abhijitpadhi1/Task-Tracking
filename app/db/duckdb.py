"""DuckDB helpers and schema creation utilities."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

import duckdb

APP_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = APP_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_DB_PATH = DATA_DIR / "tasktracker.duckdb"

SCHEMA_STATEMENTS: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS stages (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT,
        ordering INTEGER NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS repositories (
        id TEXT PRIMARY KEY,
        stage_id TEXT NOT NULL REFERENCES stages(id),
        title TEXT NOT NULL,
        description TEXT,
        ordering INTEGER NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY,
        repository_id TEXT NOT NULL REFERENCES repositories(id),
        title TEXT NOT NULL,
        description TEXT,
        ordering INTEGER NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS task_progress (
        task_id TEXT PRIMARY KEY REFERENCES tasks(id),
        completed BOOLEAN NOT NULL DEFAULT FALSE,
        completed_at TIMESTAMP,
        link TEXT
    );
    """,
    "ALTER TABLE task_progress ADD COLUMN IF NOT EXISTS link TEXT;",
)


def get_connection(read_only: bool = False) -> duckdb.DuckDBPyConnection:
    """Return a DuckDB connection, creating the DB directory if needed."""
    db_path = resolve_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(database=str(db_path), read_only=read_only)


def resolve_db_path() -> Path:
    """Resolve the DuckDB path, honoring overrides."""
    override = os.getenv("TASKTRACKER_DB_PATH")
    return Path(override) if override else DEFAULT_DB_PATH


def init_db() -> None:
    """Ensure the DuckDB schema exists."""
    with get_connection() as conn:
        _execute_statements(conn, SCHEMA_STATEMENTS)


def _execute_statements(
    conn: duckdb.DuckDBPyConnection,
    statements: Iterable[str],
) -> None:
    for statement in statements:
        conn.execute(statement)

