# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a progressive FastAPI learning repository. Each numbered folder (`FastAPI-02` through `FastAPI-11-Authorization-main`) builds on the previous one, all implementing the same **blog app** (Users + Posts) with increasing complexity.

## Running a module

All modules use `uv`. Run from within the module's directory:

```bash
cd FastAPI-05-Database   # or whichever module
uv run fastapi dev main.py
```

- API docs: `http://127.0.0.1:8000/docs`
- **FastAPI-08-Routers** requires copying `.env.example` to `.env` first
- **FastAPI-10/11** also use pydantic-settings and require environment configuration

## Quality checks (FastAPI-08-Routers only)

```bash
uv run ruff check .      # lint
uv run mypy app          # type check
uv run pytest            # run all tests
uv run pytest tests/test_health.py   # run a single test file
```

## Database migrations (FastAPI-08-Routers only)

```bash
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head
```

## Architecture progression

| Module | Key addition |
|---|---|
| FastAPI-02/03 | Jinja2 templates, no DB |
| FastAPI-04-Pydantic | Pydantic schemas |
| FastAPI-05-Database | Sync SQLAlchemy + SQLite, REST API + HTML views |
| FastAPI-06-Complete-Crud | Full CRUD (PUT/PATCH/DELETE) |
| FastAPI-07-Async | Async SQLAlchemy (`aiosqlite`), `selectinload` for relationships |
| FastAPI-08-Routers | App factory pattern, `app/` package, Alembic, JWT, pydantic-settings, ruff/mypy/pytest |
| FastAPI-09-Frontend-Forms | Routers split into `routers/` dir, HTMX frontend forms |
| FastAPI-10-Authentication | JWT auth via `pyjwt`, OAuth2PasswordBearer, password hashing with `pwdlib[argon2]`, `SecretStr` for secrets |
| FastAPI-11-Authorization | Extends 10 with `get_current_user()` dependency for route-level access control |

## Shared patterns across modules

**Data models** — Two SQLAlchemy ORM models:
- `User`: `id`, `username` (unique), `email` (unique), `image_file` (nullable); has `image_path` property. FastAPI-10+ adds `password_hash`.
- `Post`: `id`, `title`, `content`, `user_id` (FK → users), `date_posted`; `cascade="all, delete-orphan"` on the User side

**Schemas** — Pydantic v2 with base/create/update/response split. Response schemas use `ConfigDict(from_attributes=True)`. Partial updates use `model_dump(exclude_unset=True)`. FastAPI-10+ splits user responses into `UserPublic` (no email) and `UserPrivate` (includes email).

**Dual interface** — Every module serves both a Jinja2 HTML frontend (routes without `/api` prefix) and a JSON REST API (`/api/users`, `/api/posts`). Exception handlers route errors to JSON for `/api/*` paths and to `error.html` otherwise.

**Database session** — `get_db()` dependency yields a session via context manager. Async modules (`07`+) use `AsyncSession` + `create_async_engine`. The `database_url` for async SQLite is `sqlite+aiosqlite:///./blog.db`.

**Async gotchas** (FastAPI-07+):
- All DB operations must be `await`ed (`db.execute()`, `db.commit()`, `db.refresh()`, `db.delete()`)
- Use `selectinload()` for eager loading relationships to prevent N+1 queries
- After commit, explicitly refresh related attributes: `await db.refresh(obj, attribute_names=["author"])`

**Auth patterns** (FastAPI-10+):
- JWT token endpoint at `/api/users/token`, returns `{"access_token", "token_type"}`
- Case-insensitive email lookups via `func.lower()`
- Password validation enforces `min_length=8`
- Note: FastAPI-08 uses `python-jose` for JWT; FastAPI-10/11 use `pyjwt` instead

## FastAPI-08-Routers structure (production layout)

```
app/
  main.py          # create_app() factory, lifespan, CORS, router wiring
  core/
    config.py      # Settings (pydantic-settings, reads .env), cached via @lru_cache
    security.py    # password hashing + JWT helpers
  db/
    base.py        # DeclarativeBase
    session.py     # async engine + get_db dependency
  models/          # SQLAlchemy ORM models
  schemas/         # Pydantic request/response models
  api/
    router.py      # aggregates all sub-routers under /api/v1
    routes/        # individual route files (health, users, posts)
    deps.py        # shared dependencies (DbSession type alias)
tests/
alembic/
main.py            # thin entry point: `from app.main import app`
```

## Security

- Never read, print, or expose the contents of `.env` files
- Never commit `.env` files
- Settings are environment-driven. Key env vars: `DATABASE_URL`, `SECRET_KEY`, `APP_ENV`, `DEBUG`, `CORS_ORIGINS`
