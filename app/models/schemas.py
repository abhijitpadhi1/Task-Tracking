"""Pydantic schemas for API responses."""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class Task(BaseModel):
    id: str
    repository_id: str
    title: str
    description: str | None = None
    ordering: int
    completed: bool = False
    enabled: bool = False
    link: str | None = None


class ProgressMetrics(BaseModel):
    completed: int = 0
    total: int = 0
    percent: float = Field(0, ge=0, le=100)


class Repository(BaseModel):
    id: str
    stage_id: str
    title: str
    description: str | None = None
    ordering: int
    tasks: List[Task] = Field(default_factory=list)
    progress: ProgressMetrics = Field(default_factory=ProgressMetrics)


class Stage(BaseModel):
    id: str
    title: str
    description: str | None = None
    ordering: int
    repositories: List[Repository] = Field(default_factory=list)
    progress: ProgressMetrics = Field(default_factory=ProgressMetrics)


class ProgressSummary(BaseModel):
    stages: List[Stage]
    overall_progress: float = Field(0, ge=0, le=100)


class TaskProgressUpdate(BaseModel):
    completed: bool
    link: str | None = None

