# FastAPI Starter (uv)

This folder now includes a production-style FastAPI starter layout.

## Quick Start

```bash
cd FastAPI-08-Routers
uv sync
copy .env.example .env
uv run fastapi dev main.py
```

Open:
- API docs: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/api/v1/health`

## Project Layout

- `app/main.py`: app factory + middleware + router wiring
- `app/core/config.py`: environment-based settings
- `app/core/security.py`: password hashing + JWT helpers
- `app/db/`: SQLAlchemy base + async session
- `app/models/`: ORM models
- `app/schemas/`: Pydantic request/response models
- `app/api/routes/`: versioned API endpoints
- `tests/`: pytest baseline
- `alembic/`: migration scaffold

## Database Migrations

Initialize a migration:

```bash
uv run alembic revision --autogenerate -m "init"
uv run alembic upgrade head
```

## Quality Checks

```bash
uv run ruff check .
uv run mypy app
uv run pytest
```

