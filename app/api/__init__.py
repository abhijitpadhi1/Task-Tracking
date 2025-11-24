"""API routers for the Task Tracking backend."""

from fastapi import APIRouter

from .routes import router as core_router

api_router = APIRouter()
api_router.include_router(core_router, prefix="/v1")

__all__ = ["api_router"]

