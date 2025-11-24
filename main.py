"""Convenience launcher for local development."""

import uvicorn


def main() -> None:
    """Start the FastAPI server with auto-reload."""
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
