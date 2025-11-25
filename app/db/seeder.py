"""Utilities to seed the DuckDB database with static checklist data."""

from __future__ import annotations

import json

from app.db.duckdb import get_connection


def _load_stages_from_db() -> list[dict] | None:
    """Load checklist stages from DuckDB metadata table. Returns None if not found."""
    with get_connection() as conn:
        try:
            result = conn.execute(
                """
                SELECT value_json
                FROM checklist_metadata
                WHERE key = 'stages';
                """
            ).fetchone()
        except Exception:
            # Table doesn't exist or other error
            return None

        if result is None:
            return None

        return json.loads(result[0])


def seed_static_data() -> None:
    """Seed the DuckDB database with the static checklist if missing."""
    # Check if data already exists
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT COUNT(*) FROM stages;"
        ).fetchone()[0]
        if existing > 0:
            return  # Already seeded

    # Load from DuckDB metadata table
    stages = _load_stages_from_db()

    # Fallback: load from Python and store in DB for next time
    if stages is None:
        try:
            from app.data.checklist import STAGES
            stages = STAGES

            # Store in metadata table for future use
            import datetime
            with get_connection() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS checklist_metadata (
                        key TEXT PRIMARY KEY,
                        value_json TEXT NOT NULL,
                        updated_at TIMESTAMP
                    );
                    """
                )
                conn.execute(
                    """
                    INSERT INTO checklist_metadata (key, value_json, updated_at)
                    VALUES ('stages', ?, ?)
                    ON CONFLICT (key) DO UPDATE
                    SET value_json = excluded.value_json,
                        updated_at = excluded.updated_at;
                    """,
                    (json.dumps(stages, indent=2), datetime.datetime.now()),
                )
        except ImportError:
            raise RuntimeError(
                "Checklist data not available. "
                "Run: uv run python scripts/migrate_checklist_to_db.py"
            )

    with get_connection() as conn:
        for stage in stages:
            conn.execute(
                """
                INSERT INTO stages (id, title, description, ordering)
                VALUES (?, ?, ?, ?)
                ON CONFLICT (id) DO NOTHING;
                """,
                (
                    stage["id"],
                    stage["title"],
                    stage["description"],
                    stage["ordering"],
                ),
            )

            for repo in stage["repositories"]:
                conn.execute(
                    """
                    INSERT INTO repositories (id, stage_id, title, description, ordering)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT (id) DO NOTHING;
                    """,
                    (
                        repo["id"],
                        repo["stage_id"],
                        repo["title"],
                        repo["description"],
                        repo["ordering"],
                    ),
                )

                for task in repo["tasks"]:
                    conn.execute(
                        """
                        INSERT INTO tasks (id, repository_id, title, description, ordering)
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT (id) DO NOTHING;
                        """,
                        (
                            task["id"],
                            repo["id"],
                            task["title"],
                            task["description"],
                            task["ordering"],
                        ),
                    )
                    conn.execute(
                        """
                        INSERT INTO task_progress (task_id, completed, completed_at)
                        SELECT ?, FALSE, NULL
                        WHERE NOT EXISTS (
                            SELECT 1 FROM task_progress WHERE task_id = ?
                        );
                        """,
                        (task["id"], task["id"]),
                    )

