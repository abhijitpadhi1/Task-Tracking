## Task Tracking Dashboard

Single-user progress tracker for a 20-repository ML learning roadmap. The app
stores official stage/repo/task metadata in DuckDB, enforces sequential task
completion, and renders a FastAPI-served HTML/CSS/JS dashboard with a coding
checklist tab.

### Key Features
- 20 repository checklists grouped into 5 stages (including bonus stage)
- Sequential gating: a task can only be completed after all previous tasks
- Dashboard cards with stage/repo progress + global completion badge
- Dedicated “✅ Coding Checklist” tab with local-storage persistence
- DuckDB in-app database seeded from static metadata
- FastAPI backend with JSON endpoints, pytest coverage for gating logic

### Tech Stack
- **Backend:** FastAPI, Pydantic, DuckDB
- **Frontend:** HTML, modern CSS, vanilla JS modules served via FastAPI
- **Tooling:** uv for dependency/env management, pytest for tests

### Project Layout
```
app/
  api/                # FastAPI routers
  data/               # Static checklist definitions
  db/                 # DuckDB helpers & seeders
  models/             # Pydantic schemas
static/               # CSS + JS assets
templates/            # Jinja2 templates (single index.html)
tests/                # Pytest suite for progress rules
```

### Getting Started
1. **Install dependencies**
   ```bash
   uv sync
   ```
2. **Run the dev server** (auto reload + seeding)
   ```bash
   uv run fastapi dev app/main.py
   # or
   uv run python main.py
   ```
3. Navigate to `http://127.0.0.1:8000` to access the dashboard.

> The first startup creates `data/tasktracker.duckdb` and seeds the static
> checklist. If you ever change the static definitions, delete the file to
> reseed from scratch.

### API Endpoints
- `GET /api/v1/progress` – hierarchy of stages, repositories, tasks, and
  progress metrics
- `POST /api/v1/progress/{repo_id}/{task_id}` – mark a task complete/incomplete
  (enforces sequencing)
- `GET /api/v1/health` – uptime probe

### Tests
```
uv run pytest
```
Pytest provisions a temporary DuckDB file via the `fresh_db` fixture to verify
sequential gating and hierarchy assembly.

### Coding Checklist Tab
The right-side tab shows the additional “Math + ML”, “Deep Learning”, “NLP”,
“Transformers”, and “LLM Work” lists provided by the user. Checkboxes persist in
`localStorage`, independent from the main DuckDB-backed progress.

