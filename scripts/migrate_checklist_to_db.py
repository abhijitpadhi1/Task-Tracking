"""One-time migration: Export checklist.py data to DuckDB for future reads."""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.data.checklist import STAGES
from app.db.duckdb import get_connection, init_db


def migrate() -> None:
    """Store checklist metadata in DuckDB as JSON for future reference."""
    init_db()
    with get_connection() as conn:
        # Create a metadata table to store the raw checklist structure
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS checklist_metadata (
                key TEXT PRIMARY KEY,
                value_json TEXT NOT NULL,
                updated_at TIMESTAMP
            );
            """
        )

        # Store the entire STAGES structure as JSON
        import datetime
        now = datetime.datetime.now()
        conn.execute(
            """
            INSERT INTO checklist_metadata (key, value_json, updated_at)
            VALUES ('stages', ?, ?)
            ON CONFLICT (key) DO UPDATE
            SET value_json = excluded.value_json,
                updated_at = excluded.updated_at;
            """,
            (json.dumps(STAGES, indent=2), now),
        )

        print("✓ Checklist data migrated to DuckDB")
        print(f"  Stored {len(STAGES)} stages with all repositories and tasks")


if __name__ == "__main__":
    migrate()

