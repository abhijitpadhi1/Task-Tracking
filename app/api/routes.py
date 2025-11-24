"""Core API routes for the Task Tracking backend."""

from fastapi import APIRouter, HTTPException

from app.db.progress import (
    ProgressValidationError,
    fetch_progress_summary,
    update_task_progress,
)
from app.models.schemas import ProgressSummary, TaskProgressUpdate

router = APIRouter(tags=["core"])


@router.get("/health", summary="Service health probe")
async def health_check() -> dict[str, str]:
    """Return a simple health payload for uptime checks."""
    return {"status": "ok"}


@router.get(
    "/progress",
    response_model=ProgressSummary,
    summary="Full progress hierarchy",
)
async def get_progress() -> ProgressSummary:
    """Return all stages, repositories, and tasks with progress status."""
    return fetch_progress_summary()


@router.post(
    "/progress/{repo_id}/{task_id}",
    summary="Update a task's completion state",
)
async def set_task_progress(
    repo_id: str,
    task_id: str,
    payload: TaskProgressUpdate,
) -> dict[str, str]:
    """Mark a task as complete (or incomplete) with sequential validation."""
    try:
        update_task_progress(repo_id, task_id, payload.completed, payload.link)
    except ProgressValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc

    return {"status": "ok"}

