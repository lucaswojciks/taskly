# Taskly — Backend

API em FastAPI para o Taskly, um sistema de gestão de tarefas.

## Arquitetura em camadas

Cada requisição percorre uma única direção de dependências:
`api → services → repositories → models/db`. A camada **api** (`app/api`) só
fala HTTP: interpreta a requisição, chama um service e serializa a resposta —
sem regra de negócio, sem SQL. A camada **services** (`app/services`) concentra
as regras de negócio; orquestra repositories e levanta exceções de domínio, sem
conhecer HTTP nem SQL puro. A camada **repositories** (`app/repositories`) é
dona de todo o acesso a dados via queries SQLAlchemy, sem conhecer regra de
negócio. Pacotes de apoio: `models` (models SQLAlchemy), `schemas` (schemas
Pydantic de request/response), `core` (config, segurança, dependencies), `db`
(engine async + base declarativa) e `exceptions` (exceções de domínio
customizadas + um handler central que as mapeia para status HTTP, de forma que
`HTTPException` nunca aparece espalhado pelos services).

## Features implementadas

- **Auth** — registro e login (e-mail/senha), JWT, rota protegida
- **Projects** — CRUD, restrito ao dono
- **Tasks** — CRUD dentro de um projeto, mudança de status, tags associadas
- **Tags** — criação e listagem, escopadas por projeto
- **Attachments** — upload/remoção de arquivos em uma task, storage
  S3-compatible (Cloudflare R2 em produção, MinIO em desenvolvimento local)

Cada feature de negócio foi desenvolvida por Spec-Driven Development: a
especificação completa (casos de uso, contrato de API, regras de negócio) está
em [`../docs/specs/`](../docs/specs/). A documentação interativa da API
(Swagger) fica em `/docs` com o servidor rodando.

## Requisitos

- Python 3.12+
- Docker (para o Postgres e o MinIO)

## Rodando localmente

```bash
cd backend

# 1. Suba o Postgres 16 (cria também o banco taskly_test) e o MinIO
docker compose up -d

# 2. Crie e ative um virtualenv, instale as dependências
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"

# 3. Configure as variáveis de ambiente
cp .env.example .env

# 4. Aplique as migrations
alembic upgrade head

# 5. Rode a API (http://localhost:8000, docs em /docs)
uvicorn app.main:app --reload
```

Confirme que subiu: `curl http://localhost:8000/health` → `{"status":"ok"}`.

O MinIO local substitui o Cloudflare R2 para testar upload de anexos sem
depender de credenciais reais de produção — o `docker-compose.yml` já cria o
bucket automaticamente. O `.env.example` documenta as variáveis apontando para
o MinIO local por padrão.

## Migrations

```bash
alembic revision --autogenerate -m "add nova tabela"
alembic upgrade head
alembic downgrade -1
```

A URL do banco é injetada a partir de `app.core.config.settings` em
`alembic/env.py`, então o Alembic sempre usa a mesma configuração da aplicação.

## Testes

A suíte roda contra o banco `taskly_test`, separado do banco de desenvolvimento
(o `docker compose up` já cria os dois). 67 testes de integração cobrindo
health, models, auth, projects, tasks, tags e attachments.

```bash
pytest
```

`tests/conftest.py` cria todas as tabelas uma vez por sessão, envolve cada
teste numa transação com rollback no teardown (para nenhum teste ver a escrita
de outro), e fornece uma fixture `httpx.AsyncClient` já conectada à aplicação.
Os testes de attachments usam um storage fake em memória
(`tests/fake_storage.py`), injetado via override de dependency — nunca tocam
o R2/MinIO de verdade.

## Ferramentas de qualidade

```bash
ruff check .          # lint
ruff format .         # formatação
mypy app tests        # type checking estrito
pre-commit install    # roda ruff + mypy automaticamente a cada commit
```

## Deploy

`Dockerfile` (build de produção multi-stage) e `render.yaml` (Blueprint do
Render) descrevem o deploy em produção. Detalhes no README principal do
monorepo.
