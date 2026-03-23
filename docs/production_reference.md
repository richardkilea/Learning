# FastAPI Production Reference

A BluePrint for building Production ready APIs
---
## What is covered
- Full async CRUD with proper status codes (201, 204, etc.)
- JWT auth flow (register → login → Bearer token)
CORS middleware configuration
- Pydantic validation on all inputs/outputs
Public/Private response splits (control what the frontend sees)
- Proper error responses (400, 401, 403, 404, 422)
- Versioned API prefix (/api/v1) — clean separation from any frontend routes
- Pagination Frontend lists need - page=1&limit=20
-  File uploads - upload endpoint
 - Search / filtering eg  GET /api/v1/posts?author=5&q=keyword
## 0. Project Bootstrap Checklist

Follow this order when starting a new project:

- [ ] Scaffold `app/` directory structure (see [Section 2](#2-project-structure))
- [ ] Create `pyproject.toml` with core + dev dependencies (see [Section 1](#1-tech-stack))
- [ ] Create `.env.example` with all required env vars (never commit `.env`)
- [ ] Set up `Settings` class in `app/core/config.py` (see [Section 8](#8-configuration))
- [ ] Set up `DeclarativeBase` + async engine + `get_db()` in `app/db/` (see [Section 3.4](#34-database-session-management))
- [ ] Define domain models in `app/models/` (see [Section 10](#10-sqlalchemy-orm-conventions))
- [ ] Initialize Alembic and run first migration: `uv run alembic init alembic` then `uv run alembic revision --autogenerate -m "initial"`
- [ ] Define Pydantic schemas in `app/schemas/` (see [Section 4](#4-pydantic-schema-design))
- [ ] Create `app/api/deps.py` with `DbSession` type alias (see [Section 3.5](#35-dependency-injection-with-type-aliases))
- [ ] Set up custom exceptions + handlers (see [Section 9](#9-custom-exceptions))
- [ ] Wire routers in `app/api/router.py` (see [Section 3.3](#33-aggregated-router-wiring))
- [ ] Implement `create_app()` factory with lifespan + CORS (see [Section 3.1](#31-app-factory))
- [ ] Add structured logging (see [Section 11](#11-structured-logging))
- [ ] Add request ID + logging middleware (see [Section 12](#12-middleware))
- [ ] Add health check route (see [Section 13](#13-health-checks))
- [ ] Add tests (see [Section 15](#15-testing))
- [ ] Add ruff / mypy / pytest config to `pyproject.toml` (see [Section 16](#16-code-quality-config))
- [ ] Add auth when needed: security module → JWT → `CurrentUser` dependency (see [Section 5](#5-authentication--authorization))
- [ ] Dockerize (see [Section 14](#14-docker--deployment))
- [ ] Run security checklist before shipping (see [Section 17](#17-security-checklist))

---

## 1. Tech Stack

### Core

| Layer | Choice | Why |
|---|---|---|
| Framework | **FastAPI `[standard]`** (includes uvicorn, httptools, python-multipart) | Async-first, auto-generated OpenAPI docs, Pydantic-native |
| Runtime | **Python ≥ 3.12** | Pattern matching, `type` aliases, `X \| None` syntax |
| ORM | **SQLAlchemy ≥ 2.0** (async mode) | `Mapped[]` type hints, `mapped_column()`, `selectinload()` |
| DB Driver |  **asyncpg** (prod Postgres) | Non-blocking I/O |
| Migrations | **Alembic** | `--autogenerate` from ORM models |
| Validation | **Pydantic v2** (bundled with FastAPI) | `ConfigDict`, `model_dump(exclude_unset=True)` |
| Config | **pydantic-settings** + **python-dotenv** | Type-safe env vars, `.env` file loading |
| Auth | **PyJWT** + **pwdlib[argon2]** | Lightweight JWT, memory-hard password hashing |
| Package Manager | **uv** | Fast dependency resolution, managed venvs via `pyproject.toml` |

### Dev / Quality

| Tool | Config Location | Purpose |
|---|---|---|
| **ruff** | `pyproject.toml` `[tool.ruff]` | Lint + format (replaces flake8, isort, black) |
| **mypy** (strict) | `pyproject.toml` `[tool.mypy]` | Static type checking |
| **pytest** + **pytest-asyncio** | `pyproject.toml` `[tool.pytest.ini_options]` | Async test runner |
| **httpx** | test fixtures | `AsyncClient` + `ASGITransport` for in-process API testing |

---

## 2. Project Structure

```
project-root/
  main.py                         # thin entry: from app.main import app
  Dockerfile                      # production container image
  docker-compose.yml              # local dev (app + postgres + redis)
  .env.example                    # template — never commit .env
  pyproject.toml                  # deps, ruff, mypy, pytest config
  alembic.ini                     # Alembic config (points to app/db)
  alembic/
    env.py                        # async Alembic migration runner
    versions/                     # auto-generated migration scripts
  app/
    __init__.py
    main.py                       # create_app() factory, lifespan, CORS, router wiring
    core/
      __init__.py
      config.py                   # Settings (pydantic-settings), @lru_cache singleton
      security.py                 # password hashing (pwdlib) + JWT (PyJWT)
      logging.py                  # structured logging setup (structlog or stdlib)
    db/
      __init__.py
      base.py                     # DeclarativeBase
      session.py                  # async engine + AsyncSession + get_db()
    models/
      __init__.py                 # re-exports all models
      user.py
      post.py
    schemas/
      __init__.py                 # re-exports all schemas
      common.py                   # PaginatedResponse, Message, HealthResponse
      user.py                     # UserBase / Create / Update / Response
      post.py                     # PostBase / Create / Update / Response
    services/
      __init__.py
      user_service.py             # business logic for users (create, update, auth)
      post_service.py             # business logic for posts (create, update, delete)
    exceptions/
      __init__.py                 # re-exports all exception classes
      base.py                     # AppException base class
      auth.py                     # InvalidCredentials, TokenExpired
      resource.py                 # NotFound, AlreadyExists, PermissionDenied
      handlers.py                 # register_exception_handlers(app) — maps exceptions to HTTP responses
    middleware/
      __init__.py
      request_id.py               # adds X-Request-ID header to every request/response
      logging.py                  # logs method, path, status, duration per request
    api/
      router.py                   # aggregates sub-routers under /api/v1
      deps.py                     # shared Annotated type aliases (DbSession, CurrentUser)
      routes/
        __init__.py
        health.py                 # GET /health — DB connectivity + uptime check
        users.py
        posts.py
  tests/
    __init__.py
    conftest.py                   # shared fixtures (async client, test DB, test user)
    api/
      __init__.py
      test_health.py
      test_users.py
      test_posts.py
    services/
      __init__.py
      test_user_service.py
      test_post_service.py
```

**Key principles:**
- `main.py` at root is a thin entry point — all logic lives in `app/`
- Models, schemas, and routes each get their own directory with `__init__.py` re-exports
- `core/` holds cross-cutting concerns (config, security, logging)
- `api/deps.py` centralizes reusable dependency type aliases
- `services/` separates business logic from HTTP concerns — routes stay thin, logic stays testable
- `exceptions/` defines domain-specific errors — routes raise `NotFound()`, handlers map to HTTP status codes
- `middleware/` keeps request-level concerns (logging, request IDs) out of `main.py`
- `tests/` mirrors `app/` structure — `tests/api/` for route tests, `tests/services/` for unit tests

---

## 3. Architectural Patterns

### 3.1 App Factory

Centralizes app configuration, makes testing easier (swap settings, middleware, etc.).

```python
def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app

app = create_app()
```

### 3.2 Lifespan Events

Replace deprecated `@app.on_event("startup")` / `@app.on_event("shutdown")`.

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(_app: FastAPI):
    # STARTUP
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)  # dev only — use Alembic in prod
    yield
    # SHUTDOWN
    await engine.dispose()
```

Gate auto-table-creation behind a setting: `if settings.auto_create_tables:`.

### 3.3 Aggregated Router Wiring

Compose sub-routers into a single `api_router`, then mount once with a versioned prefix.

```python
# app/api/router.py
api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(posts.router, prefix="/posts", tags=["posts"])

# app/main.py
app.include_router(api_router, prefix=settings.api_v1_prefix)  # /api/v1
```

### 3.4 Database Session Management

```python
engine = create_async_engine(settings.database_url, **engine_kwargs)
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # keeps ORM objects usable after commit (critical for serialization)
)

async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session
```

**SQLite-specific:** add `connect_args={"check_same_thread": False}` to engine kwargs.

### 3.5 Dependency Injection with Type Aliases

```python
# app/api/deps.py
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[models.User, Depends(get_current_user)]

# Usage — clean, self-documenting signatures
async def create_post(post: PostCreate, db: DbSession): ...
async def update_post(post_id: int, current_user: CurrentUser, db: DbSession): ...
```

**Dependency chain for auth:**
```
CurrentUser
  └── get_current_user(token, db)
        ├── oauth2_scheme (extracts Bearer token)
        └── get_db() (yields AsyncSession, cleans up after request)
```

---

## 4. Pydantic Schema Design

### 4.1 Base / Create / Update / Response Split

```
EntityBase (shared fields)
  ├── EntityCreate(EntityBase)         # POST body — may add password, etc.
  └── EntityResponse(EntityBase)       # GET response — adds id, timestamps, nested relations
        └── EntityPrivate(EntityResponse)  # Authenticated response — adds sensitive fields

EntityUpdate (standalone)              # PATCH body — all fields Optional
```

### 4.2 Key Conventions

```python
# ORM integration
class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # reads from SQLAlchemy model attributes

# Partial updates — distinguish "not sent" from "sent as null"
class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=1, max_length=50)
    email: EmailStr | None = Field(default=None, max_length=120)

# In the route handler:
for field, value in update_data.model_dump(exclude_unset=True).items():
    setattr(db_object, field, value)

# Nested responses
class PostResponse(PostBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    date_posted: datetime
    author: UserPublic  # nested schema
```

### 4.3 Public / Private Response Split

Control what different consumers see:

```python
class UserPublic(BaseModel):   # anonymous access
    id: int
    username: str

class UserPrivate(UserPublic): # authenticated — adds sensitive fields
    email: EmailStr
```

---

## 5. Authentication & Authorization

### 5.1 JWT Flow

1. `POST /api/users` — register (password hashed with Argon2)
2. `POST /api/users/token` — login with `OAuth2PasswordRequestForm`, returns `{"access_token", "token_type"}`
3. Client sends `Authorization: Bearer <jwt>` on protected routes
4. `get_current_user()` dependency verifies JWT, loads user from DB

### 5.2 Token Handling

```python
# Creation
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key.get_secret_value(), algorithm=settings.algorithm)

# Verification — enforce required claims
def verify_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key.get_secret_value(),
            algorithms=[settings.algorithm],
            options={"require": ["exp", "sub"]},
        )
    except jwt.InvalidTokenError:
        return None
    return payload.get("sub")
```

### 5.3 Password Hashing

```python
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()  # Argon2 by default

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return password_hash.verify(plain, hashed)
```

### 5.4 Route-Level Authorization

```python
@router.patch("/{post_id}", response_model=PostResponse)
async def update_post(post_id: int, data: PostUpdate, current_user: CurrentUser, db: DbSession):
    post = ...  # fetch from DB
    if post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this post")
    # ... apply update ...
```

---

## 6. Service Layer

The service layer separates business logic from HTTP concerns. Routes stay thin (validate input, call service, return response). Services are testable without spinning up an HTTP server.

### 6.1 Service Structure

```python
# app/services/post_service.py
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import models
from app.schemas.post import PostCreate, PostUpdate
from app.exceptions import NotFound, PermissionDenied


async def create_post(db: AsyncSession, data: PostCreate, user_id: int) -> models.Post:
    user = (await db.execute(
        select(models.User).where(models.User.id == user_id)
    )).scalars().first()
    if not user:
        raise NotFound("User", user_id)

    post = models.Post(title=data.title, content=data.content, user_id=user_id)
    db.add(post)
    await db.commit()
    await db.refresh(post, attribute_names=["author"])
    return post


async def get_post(db: AsyncSession, post_id: int) -> models.Post:
    post = (await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .where(models.Post.id == post_id)
    )).scalars().first()
    if not post:
        raise NotFound("Post", post_id)
    return post


async def update_post(
    db: AsyncSession, post_id: int, data: PostUpdate, current_user_id: int
) -> models.Post:
    post = await get_post(db, post_id)
    if post.user_id != current_user_id:
        raise PermissionDenied("Not authorized to update this post")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(post, field, value)

    await db.commit()
    await db.refresh(post, attribute_names=["author"])
    return post


async def delete_post(db: AsyncSession, post_id: int, current_user_id: int) -> None:
    post = await get_post(db, post_id)
    if post.user_id != current_user_id:
        raise PermissionDenied("Not authorized to delete this post")
    await db.delete(post)
    await db.commit()


async def list_posts(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 20,
    q: str | None = None,
    author_id: int | None = None,
) -> tuple[list[models.Post], int]:
    """Returns (posts, total_count) tuple."""
    query = select(models.Post).options(selectinload(models.Post.author))

    if q:
        query = query.where(or_(
            models.Post.title.ilike(f"%{q}%"),
            models.Post.content.ilike(f"%{q}%"),
        ))
    if author_id:
        query = query.where(models.Post.user_id == author_id)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()

    posts = (await db.execute(
        query.order_by(models.Post.date_posted.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )).scalars().all()

    return posts, total
```

### 6.2 Thin Route Handlers

Routes only handle HTTP concerns — the service does the work:

```python
# app/api/routes/posts.py
from app.services import post_service

@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(data: PostCreate, current_user: CurrentUser, db: DbSession):
    return await post_service.create_post(db, data, current_user.id)

@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, db: DbSession):
    return await post_service.get_post(db, post_id)

@router.patch("/{post_id}", response_model=PostResponse)
async def update_post(post_id: int, data: PostUpdate, current_user: CurrentUser, db: DbSession):
    return await post_service.update_post(db, post_id, data, current_user.id)

@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: int, current_user: CurrentUser, db: DbSession):
    await post_service.delete_post(db, post_id, current_user.id)

@router.get("", response_model=PaginatedResponse[PostResponse])
async def list_posts(db: DbSession, pagination: Pagination, q: str | None = None, author_id: int | None = None):
    posts, total = await post_service.list_posts(db, pagination.page, pagination.per_page, q, author_id)
    return PaginatedResponse(
        data=posts, total=total, page=pagination.page,
        per_page=pagination.per_page, total_pages=-(-total // pagination.per_page),
    )
```

**Why this matters:**
- Routes are ~3 lines each — easy to read, easy to review
- Services are testable with just a DB session — no HTTP client needed
- Business rules live in one place — not scattered across routes

---

## 7. Pagination, Filtering & File Uploads

### 7.1 Pagination

**Shared schema and dependency** — define once in `app/schemas/common.py` and `app/api/deps.py`:

```python
# app/schemas/common.py
class PaginatedResponse(BaseModel, Generic[T]):
    """Wraps any list response with pagination metadata."""
    data: list[T]
    total: int
    page: int
    per_page: int
    total_pages: int

# app/api/deps.py
class PaginationParams:
    def __init__(self, page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100)):
        self.page = page
        self.per_page = per_page
        self.offset = (page - 1) * per_page

Pagination = Annotated[PaginationParams, Depends()]
```

**Usage in a route:**

```python
@router.get("", response_model=PaginatedResponse[PostResponse])
async def list_posts(db: DbSession, pagination: Pagination):
    # Count total
    total = (await db.execute(select(func.count(models.Post.id)))).scalar_one()

    # Fetch page
    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .order_by(models.Post.date_posted.desc())
        .offset(pagination.offset)
        .limit(pagination.per_page)
    )
    posts = result.scalars().all()

    return PaginatedResponse(
        data=posts,
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=-(-total // pagination.per_page),  # ceiling division
    )
```

**Frontend calls:** `GET /api/v1/posts?page=2&per_page=10`

### 7.2 Search & Filtering

**Query parameters for filtering** — add directly to route signatures:

```python
@router.get("", response_model=PaginatedResponse[PostResponse])
async def list_posts(
    db: DbSession,
    pagination: Pagination,
    q: str | None = Query(None, min_length=1, max_length=200, description="Search title/content"),
    author_id: int | None = Query(None, description="Filter by author"),
    sort: Literal["newest", "oldest"] = Query("newest"),
):
    query = select(models.Post).options(selectinload(models.Post.author))

    # Search
    if q:
        query = query.where(
            or_(
                models.Post.title.ilike(f"%{q}%"),
                models.Post.content.ilike(f"%{q}%"),
            )
        )

    # Filter
    if author_id:
        query = query.where(models.Post.user_id == author_id)

    # Sort
    order = models.Post.date_posted.desc() if sort == "newest" else models.Post.date_posted.asc()
    query = query.order_by(order)

    # Count (apply same filters, before pagination)
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    # Paginate
    result = await db.execute(query.offset(pagination.offset).limit(pagination.per_page))
    posts = result.scalars().all()

    return PaginatedResponse(data=posts, total=total, ...)
```

**Frontend calls:** `GET /api/v1/posts?q=fastapi&author_id=5&sort=newest&page=1&per_page=10`

**Rules:**
- Use `ilike` for case-insensitive search (Postgres). For SQLite, `like` is case-insensitive by default for ASCII
- Always apply filters to both the count query and the data query
- Use `Literal` types for sort/order params — self-documenting and validated automatically
- Use `Query()` with `description` — it shows up in OpenAPI docs for the frontend team

### 7.3 File Uploads

**Dependencies:** `python-multipart` (already included via `FastAPI[standard]`)

**Upload endpoint:**

```python
import shutil
from pathlib import Path
from fastapi import UploadFile

MEDIA_DIR = Path("media")
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

@router.post("/{user_id}/avatar", response_model=UserResponse)
async def upload_avatar(
    user_id: int,
    file: UploadFile,
    current_user: CurrentUser,
    db: DbSession,
):
    # Validate ownership
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Validate extension
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type not allowed. Use: {ALLOWED_EXTENSIONS}")

    # Validate size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 5 MB)")

    # Save to disk
    filename = f"user_{user_id}{ext}"
    file_path = MEDIA_DIR / filename
    MEDIA_DIR.mkdir(exist_ok=True)
    file_path.write_bytes(contents)

    # Update DB
    current_user.image_file = filename
    await db.commit()
    await db.refresh(current_user)
    return current_user
```

**Serving uploaded files:**

```python
from fastapi.staticfiles import StaticFiles

# In create_app()
app.mount("/media", StaticFiles(directory="media"), name="media")
```

**Rules:**
- Always validate file extension and size before saving
- Use a whitelist for allowed extensions, never a blacklist
- Generate deterministic filenames (e.g. `user_{id}.png`) or use UUIDs — never trust the original filename
- Serve via `StaticFiles` in dev; use a CDN or object storage (S3) in production
- Add `media/` to `.gitignore`

---

## 8. Configuration

```python
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "My API"
    app_env: Literal["dev", "test", "prod"] = "dev"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite+aiosqlite:///./app.db"
    auto_create_tables: bool = True
    secret_key: SecretStr  # no default — must come from env
    access_token_expire_minutes: int = 60
    algorithm: str = "HS256"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```

**Rules:**
- Use `SecretStr` for secrets — access via `.get_secret_value()`, prevents accidental logging
- Use `@lru_cache` to avoid re-reading env on every import
- Use `extra="ignore"` to tolerate extra env vars without errors
- Never commit `.env` files — provide `.env.example` instead

---

## 9. Custom Exceptions

### 9.1 Define Domain Exceptions

```python
# app/exceptions/base.py
class AppException(Exception):
    """Base for all application exceptions."""
    def __init__(self, detail: str = "An error occurred"):
        self.detail = detail

# app/exceptions/resource.py
from app.exceptions.base import AppException

class NotFound(AppException):
    def __init__(self, resource: str, identifier: int | str):
        self.resource = resource
        self.identifier = identifier
        super().__init__(f"{resource} with id '{identifier}' not found")

class AlreadyExists(AppException):
    def __init__(self, resource: str, field: str, value: str):
        super().__init__(f"{resource} with {field} '{value}' already exists")

class PermissionDenied(AppException):
    def __init__(self, detail: str = "You do not have permission to perform this action"):
        super().__init__(detail)

# app/exceptions/auth.py
from app.exceptions.base import AppException

class InvalidCredentials(AppException):
    def __init__(self):
        super().__init__("Incorrect email or password")  # ambiguous on purpose

class TokenExpired(AppException):
    def __init__(self):
        super().__init__("Token has expired")

# app/exceptions/__init__.py
from app.exceptions.auth import InvalidCredentials, TokenExpired
from app.exceptions.resource import AlreadyExists, NotFound, PermissionDenied
```

### 9.2 Register Exception Handlers

Map domain exceptions to HTTP responses in one place:

```python
# app/exceptions/handlers.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.exceptions.resource import NotFound, AlreadyExists, PermissionDenied
from app.exceptions.auth import InvalidCredentials, TokenExpired

def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFound)
    async def not_found_handler(request: Request, exc: NotFound) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": exc.detail})

    @app.exception_handler(AlreadyExists)
    async def already_exists_handler(request: Request, exc: AlreadyExists) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": exc.detail})

    @app.exception_handler(PermissionDenied)
    async def permission_denied_handler(request: Request, exc: PermissionDenied) -> JSONResponse:
        return JSONResponse(status_code=403, content={"detail": exc.detail})

    @app.exception_handler(InvalidCredentials)
    async def invalid_credentials_handler(request: Request, exc: InvalidCredentials) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content={"detail": exc.detail},
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(TokenExpired)
    async def token_expired_handler(request: Request, exc: TokenExpired) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content={"detail": exc.detail},
            headers={"WWW-Authenticate": "Bearer"},
        )
```

### 9.3 Wire Into App Factory

```python
# app/main.py
from app.exceptions.handlers import register_exception_handlers

def create_app() -> FastAPI:
    app = FastAPI(...)
    register_exception_handlers(app)
    # ... rest of setup
    return app
```

### 9.4 Usage in Services and Routes

```python
# In services — raise domain exceptions, not HTTPException
raise NotFound("Post", post_id)
raise AlreadyExists("User", "email", "foo@bar.com")
raise PermissionDenied("Not authorized to delete this post")
raise InvalidCredentials()

# Routes never need try/except — exceptions propagate to handlers automatically
```

**Why this matters:**
- Services don't import `HTTPException` — they stay decoupled from HTTP
- One file (`handlers.py`) maps every exception to a status code — easy to audit
- Adding a new error type = one class + one handler — no hunting through routes

---

## 10. SQLAlchemy ORM Conventions

```python
from __future__ import annotations  # enable forward references
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))

    posts: Mapped[list[Post]] = relationship(
        back_populates="author",
        cascade="all, delete-orphan",
    )

class Post(Base):
    __tablename__ = "posts"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    author: Mapped[User] = relationship(back_populates="posts")
```

**Rules:**
- Use `Mapped[]` type hints with `mapped_column()` (SQLAlchemy 2.0 style)
- Use `back_populates` (not `backref`) for explicit bidirectional relationships
- Use `cascade="all, delete-orphan"` on the parent side of one-to-many
- Use `from __future__ import annotations` for forward references

---

## 11. Structured Logging

Structured JSON logs are essential for production — they're searchable, parseable by log aggregators (Datadog, CloudWatch, ELK), and include context like request IDs.

### 11.1 Setup with stdlib

```python
# app/core/logging.py
import logging
import json
import sys
from datetime import datetime, UTC


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
        }
        # Include extra fields (request_id, user_id, etc.)
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


def setup_logging(log_level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers = [handler]

    # Quiet noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
```

### 11.2 Wire Into Lifespan

```python
# app/main.py
from app.core.logging import setup_logging

@asynccontextmanager
async def lifespan(_app: FastAPI):
    setup_logging(settings.log_level)
    logger.info("Application starting", extra={"env": settings.app_env})
    async with engine.begin() as conn:
        if settings.auto_create_tables:
            await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()
    logger.info("Application shutdown")
```

### 11.3 Config Addition

```python
# Add to Settings class
log_level: str = "INFO"  # DEBUG in dev, INFO in prod
```

---

## 12. Middleware

### 12.1 Request ID Middleware

Adds a unique ID to every request — ties logs, errors, and responses together for debugging.

```python
# app/middleware/request_id.py
import uuid
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
```

### 12.2 Request Logging Middleware

Logs method, path, status code, and duration for every request.

```python
# app/middleware/logging.py
import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        logger.info(
            "%s %s → %s (%.1fms)",
            request.method, request.url.path, response.status_code, duration_ms,
            extra={
                "request_id": getattr(request.state, "request_id", None),
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 1),
            },
        )
        return response
```

### 12.3 Wire Into App Factory

Order matters — first added = outermost wrapper:

```python
# app/main.py
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.logging import RequestLoggingMiddleware

def create_app() -> FastAPI:
    app = FastAPI(...)

    # Middleware (outermost first)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RequestIDMiddleware)  # runs first, so logging has the ID
    app.add_middleware(CORSMiddleware, ...)

    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app
```

---

## 13. Health Checks

A proper health endpoint checks that critical dependencies (DB, cache, external services) are reachable — not just that the process is running.

```python
# app/api/routes/health.py
import time
from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import DbSession
from app.schemas.common import HealthResponse

router = APIRouter()

_start_time = time.time()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: DbSession) -> HealthResponse:
    # Check DB connectivity
    db_healthy = True
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_healthy = False

    status = "healthy" if db_healthy else "degraded"
    return HealthResponse(
        status=status,
        uptime_seconds=round(time.time() - _start_time, 1),
        checks={"database": "ok" if db_healthy else "unreachable"},
    )
```

**Schema:**

```python
# Add to app/schemas/common.py
class HealthResponse(BaseModel):
    status: str                  # "healthy" | "degraded" | "unhealthy"
    uptime_seconds: float
    checks: dict[str, str]       # {"database": "ok", "redis": "ok"}
```

**Rules:**
- Mount at `/health` (not under `/api/v1`) — load balancers and orchestrators expect a fixed path
- Return 200 even when degraded — use the `status` field to communicate state
- Keep it fast — use `SELECT 1`, not a real query

---

## 14. Docker & Deployment

### 14.1 Dockerfile

```dockerfile
# --- Build stage ---
FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .
RUN uv sync --frozen --no-dev

# --- Runtime stage ---
FROM python:3.12-slim

WORKDIR /app
COPY --from=builder /app /app

# Use the venv uv created
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 14.2 docker-compose.yml (Local Dev)

```yaml
services:
  app:
    build: .
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./media:/app/media

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: blog_user
      POSTGRES_PASSWORD: blog_password
      POSTGRES_DB: blog_db
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U blog_user -d blog_db"]
      interval: 5s
      retries: 5

volumes:
  pgdata:
```

### 14.3 .env.example

```bash
# App
APP_NAME="My API"
APP_ENV=dev
DEBUG=true
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql+asyncpg://blog_user:blog_password@db:5432/blog_db

# Auth
SECRET_KEY=replace-me-with-a-long-random-secret
ACCESS_TOKEN_EXPIRE_MINUTES=60
ALGORITHM=HS256

# CORS
CORS_ORIGINS=["http://localhost:3000"]
```

### 14.4 Production Checklist

- [ ] `APP_ENV=prod`, `DEBUG=false`
- [ ] `SECRET_KEY` is a random 64+ character string
- [ ] `DATABASE_URL` points to a managed Postgres instance (not SQLite)
- [ ] Run `uv run alembic upgrade head` before starting the app (not `auto_create_tables`)
- [ ] Set `auto_create_tables=false` in production
- [ ] Use a process manager (uvicorn workers or gunicorn with uvicorn workers)
- [ ] Set up a reverse proxy (nginx / cloud load balancer) in front of uvicorn
- [ ] Configure health check endpoint in your orchestrator (Kubernetes, ECS, etc.)
- [ ] Set `LOG_LEVEL=INFO` (not DEBUG — it logs sensitive data)
- [ ] Mount `media/` on persistent storage (not the container filesystem)

---

## 15. Testing

### 15.1 Fixtures

```python
# tests/conftest.py
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import create_app
from app.db.base import Base
from app.db.session import get_db

# Use a separate test database
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
test_engine = create_async_engine(TEST_DATABASE_URL)
TestSession = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(autouse=True)
async def setup_db():
    """Create tables before each test, drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db():
    async with TestSession() as session:
        yield session


@pytest.fixture
async def client() -> AsyncClient:
    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
```

### 15.2 Route Tests

```python
# tests/api/test_users.py
async def test_create_user(client: AsyncClient):
    response = await client.post("/api/v1/users", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepassword123",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert "password" not in data  # never leak passwords in responses


async def test_create_user_duplicate_email(client: AsyncClient):
    payload = {"username": "user1", "email": "same@example.com", "password": "securepassword123"}
    await client.post("/api/v1/users", json=payload)
    response = await client.post("/api/v1/users", json={**payload, "username": "user2"})
    assert response.status_code == 409
```

### 15.3 Service Tests

```python
# tests/services/test_post_service.py
from app.services import post_service
from app.exceptions import NotFound, PermissionDenied

async def test_create_post(db_session):
    # ... create a user first ...
    post = await post_service.create_post(db_session, PostCreate(title="Test", content="Body"), user_id=user.id)
    assert post.title == "Test"
    assert post.author.id == user.id


async def test_delete_post_wrong_user(db_session):
    # ... create user + post ...
    with pytest.raises(PermissionDenied):
        await post_service.delete_post(db_session, post.id, current_user_id=999)
```

### 15.4 pytest Config

```toml
[tool.pytest.ini_options]
addopts = "-q"
asyncio_mode = "auto"
testpaths = ["tests"]
```

---

## 16. Code Quality Config

```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP"]  # pycodestyle, pyflakes, isort, bugbear, pyupgrade
ignore = ["E501"]

[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

---

## 17. Security Checklist

- [ ] `SecretStr` for all secrets in config — prevents accidental logging
- [ ] Case-insensitive email lookups: `func.lower(Model.email) == email.lower()`
- [ ] Ambiguous auth errors: `"Incorrect email or password"` — never reveal which failed
- [ ] JWT requires `["exp", "sub"]` claims via `options={"require": [...]}`
- [ ] `WWW-Authenticate: Bearer` header on 401 responses (OAuth2 spec)
- [ ] Return 403 (not 401) when user is authenticated but lacks permission
- [ ] Password validation: enforce `min_length=8` on create schemas
- [ ] Argon2 for password hashing (memory-hard, resistant to GPU attacks)
- [ ] Never commit `.env` files — add to `.gitignore`
- [ ] Never print or log secret values

---

## 18. Quick Reference Commands

| Task | Command |
|---|---|
| Run dev server | `uv run fastapi dev main.py` |
| API docs | `http://127.0.0.1:8000/docs` |
| Lint | `uv run ruff check .` |
| Format | `uv run ruff format .` |
| Type check | `uv run mypy app` |
| Run tests | `uv run pytest` |
| Single test | `uv run pytest tests/test_file.py` |
| New migration | `uv run alembic revision --autogenerate -m "description"` |
| Apply migrations | `uv run alembic upgrade head` |
| Install deps | `uv sync` |

---

## 19. Request Lifecycle (Reference)

```
1. HTTP Request
2. CORS Middleware (check Origin, add response headers)
3. Router Resolution (match URL to handler)
4. Dependency Resolution (in declaration order)
   a. OAuth2PasswordBearer → extract Bearer token
   b. get_db() → open AsyncSession
   c. get_current_user(token, db) → verify JWT, load User
5. Pydantic Validation (deserialize + validate request body)
6. Route Handler (business logic + DB operations)
7. Response Serialization (validate return against response_model)
8. Cleanup (get_db() context manager closes session)
9. HTTP Response
```


## Non -Techincal Explanation
1. Project Structure & "Scaffolding"
What it is: This is the filing system. It decides exactly where every piece of logic lives (e.g., "all security goes in the core/ folder").

The Implication: Maintainability. If a developer leaves and a new one joins, they won't spend three weeks "finding things." It prevents the code from becoming "spaghetti," which saves you massive amounts of money in long-term labor costs.

2. The Tech Stack (The "Materials")
What it is: The choice of tools like FastAPI, SQLAlchemy, and Postgres.

The Implication: Speed and Scalability. FastAPI is "async-first," which is a fancy way of saying your app can handle thousands of people clicking buttons at the same time without the server freezing up. It’s like having a 10-lane highway instead of a 1-lane country road.

3. Pydantic & Validation (The "Bouncer")
What it is: Pydantic is a tool that checks every piece of data coming into the app.

The Implication: Data Integrity. If a user tries to type "ABC" into a "Phone Number" field, Pydantic stops them instantly before that "bad data" reaches your database. This prevents the app from crashing and keeps your records clean.

4. JWT & Auth (The "Digital ID Card")
What it is: Instead of the server remembering your password every second, the server gives the user a "Token" (a JWT) after they log in.

The Implication: Security and Performance. The user carries this "badge" around. The server just checks the badge. This is industry-standard security that ensures hackers can’t easily impersonate your users.

5. Database Migrations / Alembic (The "Undo Button")
What it is: A system that tracks every change made to your database structure over time.

The Implication: Safety. If you decide to add a "Middle Name" field to your users, and it accidentally breaks something, Migrations allow you to "roll back" to exactly how the database looked 10 minutes ago. It's your insurance against data loss.

6. Service Layer (The "Middle Manager")
What it is: A dedicated space for the "business rules" (e.g., "If a user is from New York, add a 4% tax").

The Implication: Flexibility. By separating the "business rules" from the "web-parts," you can eventually build a mobile app, a website, and a desktop app that all use the same rules without rewriting them three times.

7. Structured Logging & Middleware (The "Black Box Recorder")
What it is: A system that records exactly what the server was doing right before it hit an error.

The Implication: Faster Troubleshooting. When a user says "The app isn't working," your developers don't have to guess. They can look at the "Request ID" and see exactly what went wrong in seconds. This reduces "downtime."

8. Docker (The "Shipping Container")
What it is: It wraps the entire app in a "container" that includes everything it needs to run.

The Implication: "It Works Everywhere." It eliminates the common excuse: "It worked on my computer, I don't know why it doesn't work on the server." If it works in the Docker container, it works on any cloud provider (AWS, Google, etc.).
Feature,Non-Tech Translation,Bottom Line Benefit

CRUD with Status Codes,"Standardized ""Success/Fail"" signals",Makes the frontend (the app) much easier to build.
CORS Configuration,"A ""Guest List"" for other websites",Prevents unauthorized websites from stealing your data.
Pagination,"Loading data in ""Pages"" (1, 2, 3...)",Prevents the app from slowing down when you have 1M users.
Versioning (/v1/),"""The 2026 Model""","Allows you to launch a ""v2"" later without breaking the ""v1"" app."