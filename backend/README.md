# Taskly — Backend

FastAPI service for Taskly, a task management system.

## Layered architecture

Each request flows through a single direction of dependencies:
`api → services → repositories → models/db`. The **api** layer (`app/api`) only
speaks HTTP: it parses the request, calls a service, and serializes the response
— no business rules, no SQL. The **services** layer (`app/services`) holds the
business rules; it orchestrates repositories and raises domain exceptions, and it
knows nothing about HTTP or raw SQL. The **repositories** layer
(`app/repositories`) owns all data access via SQLAlchemy queries and knows
nothing about business rules. Supporting packages: `models` (SQLAlchemy models),
`schemas` (Pydantic request/response models), `core` (config, security,
dependencies), `db` (async engine + declarative base), and `exceptions` (custom
domain errors plus one central handler that maps them to HTTP status codes, so
`HTTPException` is never scattered through the services).

## Requirements

- Python 3.12+
- Docker (for Postgres)

## Running locally

```bash
cd backend

# 1. Start Postgres 16 (also creates the taskly_test database)
docker compose up -d

# 2. Create and activate a virtualenv, install deps
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"

# 3. Configure environment
cp .env.example .env

# 4. Apply migrations (none yet — creates the alembic_version table)
alembic upgrade head

# 5. Run the API (http://localhost:8000, docs at /docs)
uvicorn app.main:app --reload
```

Check it is up: `curl http://localhost:8000/health` → `{"status":"ok"}`.

## Migrations

```bash
alembic revision --autogenerate -m "add users table"
alembic upgrade head
alembic downgrade -1
```

The database URL is injected from `app.core.config.settings` in `alembic/env.py`,
so Alembic always uses the same configuration as the app.

## Tests

The suite runs against the separate `taskly_test` database. `docker compose up`
already created it; nothing else to set up.

```bash
pytest
```

`tests/conftest.py` creates all tables once per session, wraps every test in a
transaction that is rolled back on teardown (so tests never see each other's
writes), and provides an `httpx.AsyncClient` fixture wired to the app.

## Quality tooling

```bash
ruff check .          # lint
ruff format .         # format
mypy app tests        # strict type checking
pre-commit install    # run ruff + mypy automatically on git commit
```
