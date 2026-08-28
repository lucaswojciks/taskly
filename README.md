# taskly

Sistema de gestão de tarefas — teste técnico UEX

## Monorepo layout

```
backend/      FastAPI API (Python), layered architecture — see backend/README.md
frontend/     React + Vite + TypeScript SPA — see frontend/README.md
docs/specs/   feature specs (one per feature)
render.yaml   Render Blueprint for the backend deploy
```

## CI

`.github/workflows/ci.yml` runs on every push and pull request:

- **backend** — starts a Postgres 16 service, installs the backend dependencies,
  and runs `ruff check`, `ruff format --check`, `mypy`, and `pytest`.
- **frontend** — installs dependencies (`npm ci`) and runs `npm run lint`,
  `tsc -b`, and `npm run build`.

## Deploy

The backend and frontend are deployed separately:

| Part | Platform | How |
| --- | --- | --- |
| Backend (FastAPI + Postgres) | [Render](https://render.com) | Blueprint (`render.yaml`) |
| Frontend (Vite SPA) | [Vercel](https://vercel.com) | Import the `frontend/` directory |

### Backend — Render Blueprint

`render.yaml` describes a Docker web service (`taskly-api`) and a managed
Postgres database (`taskly-db`, free plan). `backend/Dockerfile` is a multi-stage
production build that runs as a non-root user and applies database migrations
(`alembic upgrade head`) automatically on every deploy before starting uvicorn.

1. Create a Render account and connect this GitHub repository.
2. **New → Blueprint**, select the repo. Render reads `render.yaml` and shows the
   service + database it will create.
3. Apply the blueprint. The Postgres database is created and `DATABASE_URL` is
   wired to the web service automatically.
4. Open the `taskly-api` service → **Environment** and fill in the values left
   blank on purpose (they are secrets / environment-specific): `JWT_SECRET_KEY`,
   `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `BCRYPT_ROUNDS`, the `R2_*`
   variables, `ATTACHMENT_MAX_BYTES`, `ATTACHMENT_URL_TTL_SECONDS`, and
   `CORS_ORIGINS`. `CORS_ORIGINS` is a JSON array string, e.g.
   `["https://taskly.vercel.app"]`.
5. Save — Render redeploys with the new values. Health is checked at `/health`.

### Frontend — Vercel

1. Import the project on Vercel with **Root Directory** set to `frontend/`.
2. Set `VITE_API_URL` to the Render backend URL
   (e.g. `https://taskly-api.onrender.com`).
3. Deploy. Add the resulting Vercel URL to the backend's `CORS_ORIGINS`.

### ⚠️ First request is slow (Render free tier)

The backend runs on Render's **free tier**, which puts the service to sleep after
a period of inactivity. The first request after it has gone dormant takes
**roughly 30–60 seconds** while the service wakes up; subsequent requests are
fast. Initial slowness when opening the app link is expected — it is not a bug.

> Note: Render's free Postgres database is also removed 30 days after creation.
> For a longer-lived deploy, upgrade the database to a paid plan.
