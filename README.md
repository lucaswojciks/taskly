# Taskly

Sistema de gestão de tarefas — teste técnico UEX.

🔗 **Aplicação em produção:** https://taskly-olive-mu.vercel.app

> O backend roda no **free tier do Render** e "hiberna" após um período ocioso:
> a primeira requisição depois disso leva **cerca de 30–60 segundos** enquanto
> o serviço acorda. Lentidão inicial ao abrir o link é esperada — não é um bug.
> O banco Postgres do plano free também é removido 30 dias após a criação.

## Stack

**Backend** — Python 3.12 · FastAPI · SQLAlchemy 2.0 (async) · Alembic ·
Pydantic v2 · PostgreSQL 16 · JWT (PyJWT) · bcrypt · boto3 (armazenamento
S3-compatível / Cloudflare R2). Arquitetura em camadas
(`api → services → repositories → models`), com exceções de domínio e um handler
central. Qualidade: ruff, mypy (strict) e pytest.

**Frontend** — React 19 · Vite · TypeScript · Tailwind CSS v4 · shadcn/ui ·
TanStack Query · React Router · React Hook Form + Zod · axios. Lint com oxlint.

Detalhes de cada parte estão nos READMEs específicos:
[`backend/README.md`](backend/README.md) e
[`frontend/README.md`](frontend/README.md).

## Layout do monorepo

```
backend/             API FastAPI (Python), arquitetura em camadas — ver backend/README.md
frontend/            SPA React + Vite + TypeScript — ver frontend/README.md
docs/specs/          especificações das features (auth, projects-tasks-tags, attachments)
.github/workflows/   pipeline de CI (ci.yml)
render.yaml          Blueprint do Render para o deploy do backend
CLAUDE.md            instruções do projeto para o assistente de código
```

## Como rodar localmente

Pré-requisitos: **Docker** (para o Postgres e o MinIO) e **Node.js**.

```bash
# Backend — API em http://localhost:8000 (docs interativas em /docs)
cd backend
docker compose up -d                                # Postgres 16 (+ banco de testes) e MinIO
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

```bash
# Frontend — aplicação em http://localhost:5173
cd frontend
npm install
cp .env.example .env                                # VITE_API_URL aponta para http://localhost:8000
npm run dev
```

O passo a passo completo (migrations, testes, tooling de qualidade) está nos
READMEs de cada parte.

## CI

`.github/workflows/ci.yml` roda a cada push e pull request, com dois jobs em
paralelo:

- **backend** — sobe um serviço Postgres 16, instala as dependências do backend
  e executa `ruff check`, `ruff format --check`, `mypy` e `pytest`.
- **frontend** — instala as dependências (`npm ci`) e executa `npm run lint`,
  `tsc -b` e `npm run build`.

## Deploy

O backend e o frontend são publicados separadamente:

| Parte | Plataforma | Configuração |
| --- | --- | --- |
| Backend (FastAPI + Postgres) | [Render](https://render.com) | `render.yaml` (Blueprint) + `backend/Dockerfile` |
| Frontend (SPA Vite) | [Vercel](https://vercel.com) | Root Directory `frontend/` + `frontend/vercel.json` |

O `render.yaml` provisiona um serviço web Docker e um banco PostgreSQL
gerenciado (plano free); o `backend/Dockerfile` é um build de produção
multi-stage, roda como usuário não-root, e aplica migrations
(`alembic upgrade head`) automaticamente em cada deploy. No frontend,
`vercel.json` garante o fallback de rotas para uma SPA (qualquer caminho não
encontrado cai em `index.html`, deixando o React Router assumir).

Variáveis sensíveis (`JWT_SECRET_KEY`, credenciais do R2, `CORS_ORIGINS`, etc.)
não ficam no repositório — são preenchidas diretamente no painel de cada
plataforma. `CORS_ORIGINS` no backend precisa incluir a URL do frontend
publicado (ex.: `["https://taskly.vercel.app"]`), e `VITE_API_URL` no
frontend precisa apontar para a URL do backend publicado
(ex.: `https://taskly-api.onrender.com`).
