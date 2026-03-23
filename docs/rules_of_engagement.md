# Rules of Engagement

I am building a FastAPI application. I am attaching a **Production Reference Blueprint** (`production_reference.md`).

## Your Instructions

### 1. Follow the Blueprint

- The blueprint is your single source of truth for architecture, patterns, and conventions.
- Follow the **Project Structure** (Section 2) exactly — `app/core/`, `app/db/`, `app/models/`, `app/schemas/`, `app/services/`, `app/exceptions/`, `app/middleware/`, `app/api/routes/`.
- If a pattern is documented in the blueprint, use it. Do not invent alternatives.
- If something is not covered in the blueprint, ask me before deciding.

### 2. Build in Order

- Follow the **Bootstrap Checklist** (Section 0) step by step.
- Do not skip ahead. Each step depends on the previous one.
- Mark each step done and confirm with me before moving to the next.

### 3. Keep Routes Thin, Logic in Services

- Route handlers do three things only: validate input, call a service function, return the response.
- All business logic, database queries, and validation rules go in `app/services/`.
- Services raise **domain exceptions** (`NotFound`, `AlreadyExists`, `PermissionDenied`) — never `HTTPException`.
- Exception handlers in `app/exceptions/handlers.py` map domain exceptions to HTTP status codes.

### 4. Schema Discipline

- Every request and response gets a Pydantic schema. No raw dicts.
- Follow the **Base / Create / Update / Response** split (Section 4).
- Use `model_dump(exclude_unset=True)` for PATCH operations.
- Use `ConfigDict(from_attributes=True)` on all response schemas.
- Never expose sensitive fields (passwords, hashes, internal IDs) in response schemas.

### 5. Database Rules

- Async only — `AsyncSession`, `create_async_engine`, `await` all DB calls.
- Use `selectinload()` for every query that touches relationships — no lazy loading.
- After `commit()`, always `refresh()` with `attribute_names` for relationships needed in the response.
- `expire_on_commit=False` on the session factory — always.
- Migrations through Alembic — never rely on `create_all()` in production.

### 6. Auth When Required

- Follow the JWT flow in Section 5 exactly — PyJWT + pwdlib[argon2].
- Use `SecretStr` for secrets — never plain strings.
- Use `Annotated` type aliases: `DbSession`, `CurrentUser` (Section 3.5).
- Case-insensitive email lookups with `func.lower()`.
- Ambiguous error messages for auth failures — `"Incorrect email or password"`.

### 7. Every Feature Gets

- [ ] Alembic migration (if models changed)
- [ ] Pydantic schemas (create, update, response)
- [ ] Service function(s) in `app/services/`
- [ ] Route handler(s) in `app/api/routes/`
- [ ] Tests — route tests in `tests/api/`, service tests in `tests/services/`

### 8. Code Quality

- Run `ruff check .` and `mypy app` mentally before presenting code. Code you write should pass both.
- Type hints on every function signature — no `Any` unless absolutely necessary.
- Follow the ruff + mypy config in Section 16.
- No unused imports, no unused variables, no bare `except`.

### 9. Security — Non-Negotiable

- Never log, print, or expose secrets, tokens, or password hashes.
- Never commit `.env` files.
- Validate and sanitize all user input through Pydantic schemas.
- File uploads: whitelist extensions, enforce size limits, never trust original filenames.
- Follow the full **Security Checklist** (Section 17) before any deployment.

### 10. Communication Style

- Be concise. Lead with code, not explanation.
- When presenting a new file, show the full file. When modifying, show only the diff.
- If you're unsure about a design decision, present 2 options with trade-offs and let me choose.
- If I give you a feature request, confirm the plan before writing code.
- If something in the blueprint conflicts with a project-specific need, flag it — don't silently deviate.

### 11. What Not to Do

- Do not create files outside the `app/` structure unless it's a root config file (`pyproject.toml`, `Dockerfile`, `alembic.ini`).
- Do not add dependencies without telling me first.
- Do not write `HTTPException` in service files — that's what the exceptions layer is for.
- Do not use sync database operations.
- Do not skip tests. No feature is done without tests.
- Do not over-engineer. No abstractions for one-time operations. No feature flags unless I ask.
- Do not add comments explaining obvious code. Only comment where the *why* isn't self-evident.

---

## Quick Reference

| When you need to... | Go to... |
|---|---|
| Scaffold the project | Section 0 (Bootstrap Checklist) |
| Check the folder layout | Section 2 (Project Structure) |
| Write a route | Section 6 (Service Layer — thin routes) |
| Write a schema | Section 4 (Pydantic Schema Design) |
| Write a model | Section 10 (SQLAlchemy ORM Conventions) |
| Add pagination or search | Section 7 (Pagination, Filtering & File Uploads) |
| Handle errors | Section 9 (Custom Exceptions) |
| Add auth | Section 5 (Authentication & Authorization) |
| Add config/env vars | Section 8 (Configuration) |
| Add logging | Section 11 (Structured Logging) |
| Add middleware | Section 12 (Middleware) |
| Write tests | Section 15 (Testing) |
| Dockerize | Section 14 (Docker & Deployment) |
| Pre-deploy review | Section 17 (Security Checklist) |
