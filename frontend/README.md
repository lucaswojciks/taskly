# Taskly — Frontend

SPA em Vite + React + TypeScript para o Taskly.

## Stack

- **Vite** + **React 19** + **TypeScript**
- **Tailwind CSS v4** — o tema vive em `src/index.css` via `@theme` / `@theme inline`
  (sem `tailwind.config.js`). Paleta: petróleo/índigo (`brand-*`, `navy-*`) e as
  cores de status das tarefas (`status-neutral|progress|done|cancelled` + variantes
  `*-soft` para o fundo dos badges).
- **shadcn/ui** (estilo `new-york`) — componentes em `src/components/ui/`
  (button, input, textarea, card, dialog, alert-dialog, sheet, dropdown-menu,
  select, badge, sonner, avatar, tabs)
- **React Router** — rotas `/login`, `/register` e `/` (protegida; redireciona
  para `/login` quando não há token no `localStorage`)
- **TanStack Query** — `QueryClientProvider` na raiz (`src/main.tsx`), com
  `networkMode: 'always'` para que falhas de rede apareçam como erro (não fiquem
  em silêncio no estado `paused`)
- **React Hook Form + Zod** — validação de formulários (login, registro,
  criação de tarefa)
- **axios** — client centralizado em `src/lib/api.ts`

## Layout do projeto

```
src/
  components/
    auth/            painel visual compartilhado (login/registro)
    dashboard/        sidebar, criação de projeto, criação/detalhe de tarefa,
                      resumo de status
    tasks/            visão em lista, visão em kanban, badges de status/tag,
                      multi-select de tags
    ui/               componentes shadcn/ui
    protected-route.tsx
    query-error.tsx  estado de erro com botão de tentar novamente
  hooks/              use-auth, use-projects, use-tasks, use-tags,
                      use-attachments, use-task-mutations (todos via TanStack
                      Query)
  lib/                api.ts (axios + interceptors), auth.ts (token),
                      *-api.ts (chamadas por recurso: projects, tasks, tags,
                      attachments), colors.ts, status.ts, format.ts,
                      datetime.ts, utils.ts (cn)
  pages/              login, register, dashboard
  types/              tipos de domínio espelhando os schemas do backend
  index.css           import do Tailwind v4 + tokens do tema
vercel.json           rewrite de fallback para SPA (ver seção Deploy)
```

## Telas implementadas

- **Login / Registro** — formulários com validação (Zod), painel visual
  compartilhado, registro seguido de login automático.
- **Dashboard** — sidebar com projetos (rail fixo em desktop, drawer em
  mobile), criação de projeto, resumo de contadores por status, toggle entre
  visão em **Lista** e **Kanban**.
- **Criação de tarefa** — formulário completo (título, descrições, prazo,
  tags com criação inline).
- **Detalhe da tarefa** — painel de edição completo (todos os campos
  editáveis, com autosave), upload e remoção de anexos com miniatura e
  mensagens de erro específicas por tipo de falha.

## Cliente HTTP (`src/lib/api.ts`)

- URL base vinda de `VITE_API_URL`.
- Interceptor de request injeta `Authorization: Bearer <token>` do
  `localStorage`.
- Interceptor de response: em qualquer `401` de uma requisição autenticada,
  limpa o token e redireciona para `/login` (as rotas `/auth/login` e
  `/auth/register` são isentas, para que um login incorreto mostre o erro no
  formulário em vez de disparar esse redirect).
- Segue o contrato do backend: login em JSON (`POST /auth/login` com
  `{ email, password }`), e endpoints de listagem retornam um array JSON puro,
  aceitando `?limit=&offset=` (sem envelope de paginação).

## Deploy

`vercel.json` configura um rewrite de fallback (`/(.*)` → `/index.html`),
necessário porque o React Router faz roteamento client-side: sem esse
rewrite, acessar uma rota como `/login` diretamente pela URL retornaria 404
(o servidor estático tentaria achar um arquivo físico correspondente, que
não existe). Mais detalhes de deploy no README principal do monorepo.

## Rodando localmente

```bash
cd frontend

# 1. Instale as dependências
npm install

# 2. Configure a URL da API
cp .env.example .env        # ajuste VITE_API_URL se o backend não estiver em :8000

# 3. Inicie o servidor de desenvolvimento (http://localhost:5173)
npm run dev
```

Outros scripts: `npm run build` (typecheck + build de produção),
`npm run preview`, `npm run lint` (oxlint).

O backend precisa estar rodando para auth/dados funcionarem — veja
`../backend/README.md`.
