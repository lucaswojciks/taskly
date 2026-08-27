# taskly

Sistema de gestão de tarefas — teste técnico UEX

## Monorepo layout

```
backend/      FastAPI API (Python), layered architecture — see backend/README.md
frontend/     (empty for now)
docs/specs/   feature specs (one per feature)
```

## CI

`.github/workflows/ci.yml` runs on every push and pull request: it starts a
Postgres 16 service, installs the backend dependencies, and runs `ruff check`,
`ruff format --check`, `mypy`, and `pytest`.
