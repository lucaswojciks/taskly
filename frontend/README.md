# Taskly — Frontend

Vite + React + TypeScript SPA for Taskly.

## Stack

- **Vite** + **React 19** + **TypeScript**
- **Tailwind CSS v4** — theme lives in `src/index.css` via `@theme` / `@theme inline`
  (no `tailwind.config.js`). Brand palette: petrol/indigo (`brand-*`, `navy-*`) plus
  task status accents (`status-neutral|progress|done|cancelled` + `*-soft`).
- **shadcn/ui** (`new-york` style) — components in `src/components/ui/`
  (button, input, card, dialog, sheet, dropdown-menu, select, badge, sonner, avatar, tabs)
- **React Router** — `/login`, `/register`, `/` (protected; redirects to `/login`
  when there is no token in `localStorage`)
- **TanStack Query** — `QueryClientProvider` at the root (`src/main.tsx`)
- **axios** — centralised client in `src/lib/api.ts`

## Project layout

```
src/
  components/        ProtectedRoute + shadcn ui/
  hooks/             use-auth (token state helper)
  lib/               api.ts (axios + interceptors), auth.ts (token storage), utils.ts (cn)
  pages/             login, register, home  (stubs — screens come next)
  types/             domain types mirroring the backend schemas
  index.css          Tailwind v4 import + theme tokens
```

## HTTP client (`src/lib/api.ts`)

- Base URL from `VITE_API_URL`.
- Request interceptor injects `Authorization: Bearer <token>` from `localStorage`.
- Response interceptor: on any `401`, clears the token and redirects to `/login`.
- Matches the backend contract: JSON login (`POST /auth/login` with
  `{ email, password }`), and list endpoints return a plain JSON array with
  `?limit=&offset=` (no pagination envelope).

## Running locally

```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Configure the API URL
cp .env.example .env        # edit VITE_API_URL if the backend isn't on :8000

# 3. Start the dev server (http://localhost:5173)
npm run dev
```

Other scripts: `npm run build` (typecheck + production build), `npm run preview`,
`npm run lint` (oxlint).

The backend must be running for auth/data to work — see `../backend/README.md`.
