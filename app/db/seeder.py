"""Utilities to seed the DuckDB database with static checklist data."""

from __future__ import annotations

from app.data.checklist import STAGES
from app.db.duckdb import get_connection


def seed_static_data() -> None:
    """Seed the DuckDB database with the static checklist if missing."""
    with get_connection() as conn:
        for stage in STAGES:
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

