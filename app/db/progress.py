"""Progress retrieval and update helpers."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass

from app.db.duckdb import get_connection
from app.models.schemas import (
    ProgressMetrics,
    ProgressSummary,
    Repository,
    Stage,
    Task,
)


@dataclass
class ProgressValidationError(Exception):
    """Raised when sequential completion rules are violated."""

    message: str


def fetch_progress_summary() -> ProgressSummary:
    """Return the full stage -> repo -> task hierarchy with progress metrics."""
    with get_connection(read_only=True) as conn:
        cursor = conn.execute(
            """
            SELECT
                s.id AS stage_id,
                s.title AS stage_title,
                s.description AS stage_description,
                s.ordering AS stage_order,
                r.id AS repo_id,
                r.title AS repo_title,
                r.description AS repo_description,
                r.ordering AS repo_order,
                t.id AS task_id,
                t.title AS task_title,
                t.description AS task_description,
                t.ordering AS task_order,
                COALESCE(tp.completed, FALSE) AS completed,
                tp.link AS link
            FROM stages s
            JOIN repositories r ON r.stage_id = s.id
            JOIN tasks t ON t.repository_id = r.id
            LEFT JOIN task_progress tp ON tp.task_id = t.id
            ORDER BY s.ordering, r.ordering, t.ordering;
            """
        )
        columns = [desc[0] for desc in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

    stage_map: "OrderedDict[str, dict]" = OrderedDict()

    for row in rows:
        stage = stage_map.setdefault(
            row["stage_id"],
            {
                "id": row["stage_id"],
                "title": row["stage_title"],
                "description": row["stage_description"],
                "ordering": row["stage_order"],
                "repositories": OrderedDict(),
            },
        )

        repos: "OrderedDict[str, dict]" = stage["repositories"]
        repo = repos.setdefault(
            row["repo_id"],
            {
                "id": row["repo_id"],
                "stage_id": row["stage_id"],
                "title": row["repo_title"],
                "description": row["repo_description"],
                "ordering": row["repo_order"],
                "tasks": [],
            },
        )

        repo["tasks"].append(
            {
                "id": row["task_id"],
                "repository_id": row["repo_id"],
                "title": row["task_title"],
                "description": row["task_description"],
                "ordering": row["task_order"],
                "completed": bool(row["completed"]),
                "link": row["link"],
            }
        )

    stages: list[Stage] = []
    total_completed = 0
    total_tasks = 0

    for stage_data in stage_map.values():
        repos: list[Repository] = []
        stage_completed = 0
        stage_total = 0

        for repo_data in stage_data["repositories"].values():
            tasks_raw = sorted(repo_data["tasks"], key=lambda t: t["ordering"])
            tasks: list[Task] = []
            unlocked = True

            for task_data in tasks_raw:
                enabled = unlocked or task_data["completed"]
                unlocked = unlocked and task_data["completed"]
                task = Task(
                    **task_data,
                    enabled=enabled,
                )
                tasks.append(task)

            completed_count = sum(1 for task in tasks if task.completed)
            repo_total = len(tasks)
            percent = (
                round((completed_count / repo_total) * 100, 1)
                if repo_total
                else 0
            )
            progress = ProgressMetrics(
                completed=completed_count,
                total=repo_total,
                percent=percent,
            )
            repo = Repository(
                **{k: v for k, v in repo_data.items() if k != "tasks"},
                tasks=tasks,
                progress=progress,
            )
            repos.append(repo)

            stage_completed += completed_count
            stage_total += repo_total

        stage_percent = (
            round((stage_completed / stage_total) * 100, 1)
            if stage_total
            else 0
        )
        stage_progress = ProgressMetrics(
            completed=stage_completed,
            total=stage_total,
            percent=stage_percent,
        )
        stage_model = Stage(
            id=stage_data["id"],
            title=stage_data["title"],
            description=stage_data["description"],
            ordering=stage_data["ordering"],
            repositories=repos,
            progress=stage_progress,
        )
        stages.append(stage_model)

        total_completed += stage_completed
        total_tasks += stage_total

    overall = round((total_completed / total_tasks) * 100, 1) if total_tasks else 0
    return ProgressSummary(stages=stages, overall_progress=overall)


def update_task_progress(
    repo_id: str,
    task_id: str,
    completed: bool,
    link: str | None = None,
) -> None:
    """Update a task's completion state with sequential validation."""
    with get_connection() as conn:
        task_row = conn.execute(
            """
            SELECT repository_id, ordering
            FROM tasks
            WHERE id = ?
            """,
            (task_id,),
        ).fetchone()

        if task_row is None:
            raise ProgressValidationError("Task not found.")

        task_repo_id, task_order = task_row
        if task_repo_id != repo_id:
            raise ProgressValidationError("Task does not belong to repository.")

        if completed:
            blocking = conn.execute(
                """
                SELECT COUNT(*)
                FROM tasks t
                LEFT JOIN task_progress tp ON tp.task_id = t.id
                WHERE t.repository_id = ?
                  AND t.ordering < ?
                  AND COALESCE(tp.completed, FALSE) = FALSE;
                """,
                (repo_id, task_order),
            ).fetchone()[0]

            if blocking:
                raise ProgressValidationError(
                    "Complete previous tasks before unlocking this item."
                )

        if completed and not (link and link.strip()):
            raise ProgressValidationError("Provide a work link to mark complete.")

        conn.execute(
            """
            INSERT INTO task_progress (task_id, completed, completed_at, link)
            VALUES (
                ?,
                ?,
                CASE WHEN ? THEN CURRENT_TIMESTAMP ELSE NULL END,
                ?
            )
            ON CONFLICT (task_id) DO UPDATE
            SET completed = excluded.completed,
                completed_at = excluded.completed_at,
                link = CASE
                    WHEN excluded.completed = TRUE THEN excluded.link
                    ELSE NULL
                END;
            """,
            (
                task_id,
                completed,
                completed,
                link if completed else None,
            ),
        )

