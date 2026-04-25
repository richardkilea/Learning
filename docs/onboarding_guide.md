# FastAPI Learning Repository — Onboarding Guide

This is a progressive learning repository implementing a **blog app** (Users + Posts) across modules `FastAPI-02` through `FastAPI-11`. Each module layers one major concept on top of the previous. Run any module with `uv run fastapi dev main.py` from inside the module directory; API docs are always at `http://127.0.0.1:8000/docs`.

## Table of Contents

- [1. Tech Stack](#1-tech-stack)
  - [1.1 Core Dependencies](#11-core-dependencies)
  - [1.2 Dev Dependencies (FastAPI-08 only)](#12-dev-dependencies-fastapi-08-only)
  - [1.3 Package Manager](#13-package-manager)
  - [1.4 Module Progression Matrix](#14-module-progression-matrix)
- [2. Architecture & Workflow](#2-architecture--workflow)
  - [2.1 File Structures](#21-file-structures)
  - [2.2 App Factory Pattern](#22-app-factory-pattern)
  - [2.3 Lifespan Events](#23-lifespan-events)
  - [2.4 Router Wiring](#24-router-wiring)
  - [2.5 Database Session Management](#25-database-session-management)
  - [2.6 Request Lifecycle](#26-request-lifecycle)
  - [2.7 Dual Interface (HTML + JSON API)](#27-dual-interface-html--json-api)
- [3. FastAPI Patterns](#3-fastapi-patterns)
  - [3.1 Dependency Injection](#31-dependency-injection)
  - [3.2 Pydantic Schemas](#32-pydantic-schemas)
  - [3.3 Exception Handling](#33-exception-handling)
  - [3.4 CRUD Operations](#34-crud-operations)
  - [3.5 Authentication (Modules 10-11)](#35-authentication-modules-10-11)
  - [3.6 Authorization (Module 11)](#36-authorization-module-11)
  - [3.7 Configuration](#37-configuration)
- [4. Best Practices](#4-best-practices)
  - [4.1 Async Database Operations](#41-async-database-operations)
  - [4.2 Dependency Injection](#42-dependency-injection)
  - [4.3 Pydantic & Validation](#43-pydantic--validation)
  - [4.4 SQLAlchemy ORM](#44-sqlalchemy-orm)
  - [4.5 Security](#45-security)
  - [4.6 API Design](#46-api-design)
  - [4.7 Code Quality (FastAPI-08)](#47-code-quality-fastapi-08)
  - [4.8 Quick Reference Commands](#48-quick-reference-commands)

---

## 1. Tech Stack

### 1.1 Core Dependencies

| Library | Version | Purpose | Modules |
|---|---|---|---|
| FastAPI `[standard]` | `>=0.128.0` | Web framework (includes uvicorn, httptools, python-multipart) | All (02–11) |
| Python | `>=3.12` | Runtime | All |
| SQLAlchemy | `>=2.0.45` | ORM — sync in 05–06, async in 07+ | 05–11 |
| aiosqlite | `>=0.22.1` | Async SQLite driver for SQLAlchemy | 07–11 |
| greenlet | `>=3.3.0` | Required by async SQLAlchemy | 07–11 |
| Alembic | `>=1.16.5` | Database migrations | 08 |
| Pydantic v2 | (bundled with FastAPI) | Request/response validation | 04–11 |
| email-validator | `>=2.2.0` | `EmailStr` field support | 08 |
| pydantic-settings | `>=2.10.1` | Environment-driven configuration | 08, 10, 11 |
| python-dotenv | `>=1.1.1` | `.env` file loading | 08 |
| pwdlib | `>=0.3.0` | Password hashing (generic) | 08 |
| pwdlib[argon2] | `>=0.3.0` | Password hashing (Argon2 algorithm) | 10, 11 |
| python-jose[cryptography] | `>=3.5.0` | JWT encode/decode | 08 |
| PyJWT | `>=2.10.1` | JWT encode/decode (lighter alternative) | 10, 11 |
| Jinja2 | (bundled via `[standard]`) | Server-side HTML templating | All |
| Bootstrap | 5.3.8 (CDN) | Frontend CSS/JS framework | 09+ |

### 1.2 Dev Dependencies (FastAPI-08 only)

| Library | Version | Purpose |
|---|---|---|
| ruff | `>=0.13.2` | Linter + formatter |
| mypy | `>=1.18.2` | Static type checker |
| pytest | `>=8.4.2` | Test runner |
| pytest-asyncio | `>=1.2.0` | Async test support |
| httpx | `>=0.28.1` | Async HTTP client for testing |

### 1.3 Package Manager

All modules use **uv** (not pip). Dependencies are declared in `pyproject.toml`. Running `uv run fastapi dev main.py` auto-installs dependencies into a managed virtual environment.

### 1.4 Module Progression Matrix

| Module | Key Concept | Sync/Async | DB | Auth | Config | Quality |
|---|---|---|---|---|---|---|
| 02–03 | Jinja2 templates | sync | — | — | — | — |
| 04 | Pydantic schemas | sync | — | — | — | — |
| 05 | SQLAlchemy + CRUD | sync | SQLite | — | — | — |
| 06 | Full CRUD (PUT/PATCH/DELETE) | sync | SQLite | — | — | — |
| 07 | Async SQLAlchemy | **async** | aiosqlite | — | — | — |
| 08 | Production layout | async | aiosqlite + Alembic | JWT (python-jose) | pydantic-settings | ruff, mypy, pytest |
| 09 | HTMX frontend forms | async | aiosqlite | — | — | — |
| 10 | Authentication | async | aiosqlite | JWT (PyJWT) + Argon2 | pydantic-settings | — |
| 11 | Authorization | async | aiosqlite | JWT (PyJWT) + Argon2 + `get_current_user` | pydantic-settings | — |

---

## 2. Architecture & Workflow

### 2.1 File Structures

**FastAPI-08 — Production Layout**

```
FastAPI-08-Routers/
  main.py                     # thin entry: from app.main import app
  app/
    main.py                   # create_app() factory, lifespan, CORS, router wiring
    core/
      config.py               # Settings (pydantic-settings), @lru_cache
      security.py             # password hashing (pwdlib) + JWT (python-jose)
    db/
      base.py                 # DeclarativeBase
      session.py              # async engine + AsyncSession + get_db()
    models/
      __init__.py             # re-exports User, Post
      user.py
      post.py
    schemas/
      __init__.py             # re-exports all schemas
      common.py               # Message
      user.py                 # UserBase / Create / Update / Response
      post.py                 # PostBase / Create / Update / Response
    api/
      router.py               # aggregates sub-routers under /api/v1
      deps.py                 # DbSession = Annotated[AsyncSession, Depends(get_db)]
      routes/
        health.py
        users.py
        posts.py
  tests/
    conftest.py               # async client fixture
    test_health.py
  alembic/
    env.py                    # async Alembic migration runner
```

**FastAPI-10/11 — Simpler Layout**

```
FastAPI-11-Authorization-main/
  main.py            # app instance, lifespan, HTML routes, exception handlers
  database.py        # engine + Base + get_db()
  models.py          # User + Post ORM models
  schemas.py         # all Pydantic schemas (flat file)
  auth.py            # password hashing, JWT, OAuth2, get_current_user, CurrentUser
  config.py          # Settings (pydantic-settings + SecretStr)
  routers/
    users.py         # /api/users — registration, token, CRUD
    posts.py         # /api/posts — CRUD with ownership checks
  templates/         # Jinja2 HTML
  static/            # CSS, JS, icons
  media/             # uploaded files
```

### 2.2 App Factory Pattern

From `FastAPI-08-Routers/app/main.py`:

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

FastAPI-10/11 skip the factory and create `app = FastAPI(lifespan=lifespan)` directly at module level.

### 2.3 Lifespan Events

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(_app: FastAPI):
    # STARTUP: create tables (dev convenience — use Alembic in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # SHUTDOWN: dispose connection pool
    await engine.dispose()
```

FastAPI-08 adds a conditional gate: `if settings.auto_create_tables:` before table creation.

### 2.4 Router Wiring

**Aggregated (FastAPI-08)** — sub-routers are composed into a single `api_router`, then mounted once:

```python
# app/api/router.py
api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(posts.router, prefix="/posts", tags=["posts"])

# app/main.py
app.include_router(api_router, prefix=settings.api_v1_prefix)  # /api/v1
```

**Direct (FastAPI-10/11)** — routers mounted straight onto the app:

```python
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(posts.router, prefix="/api/posts", tags=["posts"])
```

### 2.5 Database Session Management

From `FastAPI-08-Routers/app/db/session.py`:

```python
engine_kwargs: dict[str, object] = {"future": True}
if settings.database_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}  # required for SQLite

engine = create_async_engine(settings.database_url, **engine_kwargs)
SessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False  # prevents lazy-load surprises
)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session  # session is cleaned up after the request completes
```

> **Key settings:** `expire_on_commit=False` keeps ORM objects usable after `commit()` (critical for response serialization). `check_same_thread=False` is required for SQLite in async mode.

### 2.6 Request Lifecycle

```
Request Lifecycle (FastAPI-11, authorized endpoint)
====================================================

1. HTTP Request arrives
       |
2. CORS Middleware
       |  checks Origin header, adds response headers
       |
3. Router Resolution
       |  matches URL path to route handler
       |
4. Dependency Resolution (in declaration order)
       |  a. OAuth2PasswordBearer — extracts Bearer token from Authorization header
       |  b. get_db() — opens AsyncSession via context manager
       |  c. get_current_user(token, db) — verifies JWT, loads User from DB
       |
5. Pydantic Validation
       |  deserializes + validates request body against schema
       |  (raises RequestValidationError on failure)
       |
6. Route Handler
       |  executes business logic + database operations
       |
7. Response Serialization
       |  validates return value against response_model (Pydantic)
       |
8. Cleanup
       |  get_db() context manager closes/returns session to pool
       |
9. HTTP Response sent
```

### 2.7 Dual Interface (HTML + JSON API)

Every module serves both a Jinja2 HTML frontend and a JSON REST API. The two interfaces are separated by:

- **HTML routes** use `include_in_schema=False` to hide from OpenAPI docs
- **API routes** are mounted under `/api/` prefixes
- **Exception handlers** check the request path to decide JSON vs HTML error response:

```python
@app.exception_handler(StarletteHTTPException)
async def general_http_exception_handler(request: Request, exception: StarletteHTTPException):
    if request.url.path.startswith("/api"):
        return await http_exception_handler(request, exception)  # default JSON response

    return templates.TemplateResponse(
        request, "error.html",
        {"status_code": exception.status_code, "title": exception.status_code,
         "message": exception.detail or "An error occurred."},
        status_code=exception.status_code,
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exception: RequestValidationError):
    if request.url.path.startswith("/api"):
        return await request_validation_exception_handler(request, exception)

    return templates.TemplateResponse(
        request, "error.html",
        {"status_code": 422, "title": 422,
         "message": "Invalid request. Please check your input and try again."},
        status_code=422,
    )
```

---

## 3. FastAPI Patterns

### 3.1 Dependency Injection

**Type aliases** make dependency signatures reusable and concise:

```python
# FastAPI-08: app/api/deps.py
DbSession = Annotated[AsyncSession, Depends(get_db)]

# FastAPI-11: auth.py
CurrentUser = Annotated[models.User, Depends(get_current_user)]
```

**Usage in routes:**

```python
async def create_post(post: PostCreate, db: DbSession):                # DB only
async def update_post(post_id: int, current_user: CurrentUser, db: DbSession):  # auth + DB
```

**Dependency chain** — `CurrentUser` chains through multiple layers:

```
CurrentUser
  └── get_current_user(token, db)
        ├── oauth2_scheme (extracts Bearer token from header)
        └── get_db() (creates AsyncSession, yields, then cleans up)
```

**Yield dependencies** — `get_db()` is a generator that yields a session and cleans up after the request:

```python
async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session  # request runs here; cleanup happens after
```

### 3.2 Pydantic Schemas

**Schema hierarchy** — Base/Create/Update/Response split with auth-aware variants:

```
UserBase (username, email)
  ├── UserCreate(UserBase)          # POST body — adds password field (modules 10+)
  └── UserPublic(BaseModel)         # GET response — id, username, image_file, image_path
        └── UserPrivate(UserPublic) # Authenticated response — adds email

UserUpdate (standalone)             # PATCH body — all fields Optional

PostBase (title, content)
  ├── PostCreate(PostBase)          # POST body
  └── PostResponse(PostBase)        # GET response — adds id, user_id, date_posted, author

PostUpdate (standalone)             # PATCH body — all fields Optional

Token (access_token, token_type)    # Login response
```

**Key conventions from `FastAPI-11-Authorization-main/schemas.py`:**

```python
# ORM integration — allows Pydantic to read from SQLAlchemy model attributes
class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    image_file: str | None
    image_path: str

# Public/Private split — control what authenticated vs anonymous users see
class UserPrivate(UserPublic):
    email: EmailStr

# Partial updates — all fields Optional with validation constraints
class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=1, max_length=50)
    email: EmailStr | None = Field(default=None, max_length=120)
    image_file: str | None = Field(default=None, min_length=1, max_length=200)

# Nested response — PostResponse includes author as a nested UserPublic
class PostResponse(PostBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    date_posted: datetime
    author: UserPublic
```

### 3.3 Exception Handling

Two exception types are handled with path-based routing (see [2.7](#27-dual-interface-html--json-api)):

- **`StarletteHTTPException`** — raised by `HTTPException(status_code=404, detail="Not found")` in route handlers
- **`RequestValidationError`** — raised automatically by Pydantic when request body/params are invalid

Standard usage in routes:

```python
# 404 for missing resources
raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

# 400 for business rule violations
raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")

# 401 for auth failures (include WWW-Authenticate header per OAuth2 spec)
raise HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid or expired token",
    headers={"WWW-Authenticate": "Bearer"},
)

# 403 for authorization failures (authenticated but not permitted)
raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this post")
```

### 3.4 CRUD Operations

CRUD is implemented **directly in route handlers** (no repository/service layer). From `FastAPI-08-Routers/app/api/routes/posts.py`:

**Create (POST):**

```python
@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(post: PostCreate, db: DbSession):
    user = (await db.execute(
        select(models.User).where(models.User.id == post.user_id)
    )).scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    new_post = models.Post(title=post.title, content=post.content, user_id=post.user_id)
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post, attribute_names=["author"])  # eager-load relationship for response
    return new_post
```

**Partial Update (PATCH) — using `model_dump(exclude_unset=True)`:**

```python
@router.patch("/{post_id}", response_model=PostResponse)
async def update_post_partial(post_id: int, post_data: PostUpdate, db: DbSession):
    post = (await db.execute(
        select(models.Post).where(models.Post.id == post_id)
    )).scalars().first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    for field, value in post_data.model_dump(exclude_unset=True).items():
        setattr(post, field, value)

    await db.commit()
    await db.refresh(post, attribute_names=["author"])
    return post
```

**Read with N+1 prevention — using `selectinload`:**

```python
result = await db.execute(
    select(models.Post)
    .options(selectinload(models.Post.author))  # eager-load in a single query
    .order_by(models.Post.date_posted.desc()),
)
posts = result.scalars().all()
```

**Delete:**

```python
@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: int, db: DbSession):
    post = (await db.execute(
        select(models.Post).where(models.Post.id == post_id)
    )).scalars().first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    await db.delete(post)
    await db.commit()
```

### 3.5 Authentication (Modules 10-11)

**JWT flow:**

1. User registers via `POST /api/users` (password hashed with Argon2)
2. User logs in via `POST /api/users/token` with `OAuth2PasswordRequestForm`
3. Server returns `{"access_token": "<jwt>", "token_type": "bearer"}`
4. Client sends `Authorization: Bearer <jwt>` on protected requests
5. `get_current_user()` verifies JWT, loads user from DB

**Token creation** (from `FastAPI-11-Authorization-main/auth.py`):

```python
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode,
        settings.secret_key.get_secret_value(),  # SecretStr prevents accidental logging
        algorithm=settings.algorithm,
    )
```

**Token verification:**

```python
def verify_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key.get_secret_value(),
            algorithms=[settings.algorithm],
            options={"require": ["exp", "sub"]},  # enforce required claims
        )
    except jwt.InvalidTokenError:
        return None
    else:
        return payload.get("sub")
```

**Password hashing** (pwdlib with Argon2):

```python
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)
```

**Case-insensitive email lookups:**

```python
result = await db.execute(
    select(models.User).where(func.lower(models.User.email) == form_data.username.lower()),
)
```

### 3.6 Authorization (Module 11)

The `CurrentUser` type alias enforces authentication on any route that declares it:

```python
# auth.py
CurrentUser = Annotated[models.User, Depends(get_current_user)]

# routers/posts.py — ownership check
@router.patch("/{post_id}", response_model=PostResponse)
async def update_post_partial(
    post_id: int,
    post_data: PostUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # ... fetch post ...
    if post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this post")
    # ... apply update ...
```

### 3.7 Configuration

**FastAPI-08 — `@lru_cache` singleton** (from `app/core/config.py`):

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "FastAPI Blog API"
    app_env: Literal["dev", "test", "prod"] = "dev"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite+aiosqlite:///./blog.db"
    auto_create_tables: bool = True
    secret_key: str = "replace-me-with-a-long-random-secret"
    access_token_expire_minutes: int = 60
    algorithm: str = "HS256"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

**FastAPI-11 — Module-level with `SecretStr`** (from `config.py`):

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    secret_key: SecretStr          # no default — must come from .env
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

settings = Settings()  # type: ignore[call-arg]
```

Access secrets safely: `settings.secret_key.get_secret_value()` — `SecretStr` prevents accidental exposure in logs and repr output.

---

## 4. Best Practices

### 4.1 Async Database Operations

- Always `await` database calls: `db.execute()`, `db.commit()`, `db.refresh()`, `db.delete()`
- Use `selectinload()` for eager loading relationships to prevent N+1 queries
- After commit, explicitly refresh relationship attributes: `await db.refresh(obj, attribute_names=["author"])`
- Set `expire_on_commit=False` on the session factory to keep objects usable after commit

### 4.2 Dependency Injection

- Use `Annotated` type aliases (`DbSession`, `CurrentUser`) for reusable dependency declarations
- Use generator (`yield`) dependencies for session lifecycle management
- Chain dependencies for auth: `oauth2_scheme` → `get_current_user` → `CurrentUser`

### 4.3 Pydantic & Validation

- Use the Base/Create/Update/Response schema split pattern
- Use `ConfigDict(from_attributes=True)` on response schemas (Pydantic v2, not the legacy inner `Config` class)
- Use `model_dump(exclude_unset=True)` for PATCH to distinguish "not sent" from "sent as null"
- Use `SecretStr` for sensitive config values; access via `.get_secret_value()`
- Use `Field()` with `min_length`, `max_length` for validation constraints

### 4.4 SQLAlchemy ORM

- Use modern SQLAlchemy 2.0 `Mapped` type hints with `mapped_column()`
- Use `cascade="all, delete-orphan"` on the parent side of one-to-many relationships
- Use `back_populates` (not `backref`) for explicit bidirectional relationships
- Use `from __future__ import annotations` for forward references in model files

### 4.5 Security

- Case-insensitive email lookups: `func.lower(models.User.email) == email.lower()`
- Ambiguous error messages: `"Incorrect email or password"` — never reveal which credential failed
- JWT requires `["exp", "sub"]` claims via `options={"require": ["exp", "sub"]}`
- `SecretStr` prevents accidental secret exposure in logs/repr

### 4.6 API Design

- Use `include_in_schema=False` for HTML routes to keep OpenAPI docs clean
- Use path-based exception routing for dual (HTML + JSON) interfaces
- Use `status_code=status.HTTP_201_CREATED` for POST, `HTTP_204_NO_CONTENT` for DELETE
- Return 403 (not 401) for authorization failures when the user is authenticated but lacks permission

### 4.7 Code Quality (FastAPI-08)

```toml
# ruff — linter + formatter
[tool.ruff]
line-length = 100
target-version = "py312"
[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP"]  # pycodestyle, pyflakes, isort, bugbear, pyupgrade
ignore = ["E501"]

# mypy — static type checker (strict)
[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

# pytest — async test runner
[tool.pytest.ini_options]
addopts = "-q"
asyncio_mode = "auto"
testpaths = ["tests"]
```

Tests use `httpx.AsyncClient` with `ASGITransport` (not `TestClient`):

```python
@pytest.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client
```

### 4.8 Quick Reference Commands

| Task | Command |
|---|---|
| Run any module | `cd <module-dir> && uv run fastapi dev main.py` |
| API docs | `http://127.0.0.1:8000/docs` |
| Lint (08) | `uv run ruff check .` |
| Type check (08) | `uv run mypy app` |
| Run tests (08) | `uv run pytest` |
| Single test file (08) | `uv run pytest tests/test_health.py` |
| New migration (08) | `uv run alembic revision --autogenerate -m "description"` |
| Apply migrations (08) | `uv run alembic upgrade head` |
