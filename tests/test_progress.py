"""Tests for progress aggregation and sequential validation."""

from __future__ import annotations

import pytest

from app.db.progress import (
    ProgressValidationError,
    fetch_progress_summary,
    update_task_progress,
)


def test_progress_summary_contains_all_repositories(fresh_db):
    summary = fetch_progress_summary()
    assert len(summary.stages) == 5
    total_repos = sum(len(stage.repositories) for stage in summary.stages)
    assert total_repos == 20
    assert summary.overall_progress == 0


def test_tasks_require_sequential_completion(fresh_db):
    summary = fetch_progress_summary()
    repo = summary.stages[0].repositories[0]
    first_task = repo.tasks[0]
    second_task = repo.tasks[1]

    with pytest.raises(ProgressValidationError):
        update_task_progress(repo.id, second_task.id, True, "https://example.com/second")

    update_task_progress(repo.id, first_task.id, True, "https://example.com/first")
    update_task_progress(repo.id, second_task.id, True, "https://example.com/second")

    summary = fetch_progress_summary()
    repo = summary.stages[0].repositories[0]
    assert repo.tasks[0].completed is True
    assert repo.tasks[1].completed is True
    assert repo.tasks[1].link == "https://example.com/second"


def test_link_required_for_completion(fresh_db):
    summary = fetch_progress_summary()
    repo = summary.stages[0].repositories[0]
    first_task = repo.tasks[0]

    with pytest.raises(ProgressValidationError):
        update_task_progress(repo.id, first_task.id, True, "")

