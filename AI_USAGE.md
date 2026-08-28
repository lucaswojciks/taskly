# Uso de IA no desenvolvimento — Taskly

Este documento registra como usei ferramentas de IA (Claude Code) ao longo do desenvolvimento, incluindo prompts, o que foi gerado, e a revisão crítica feita sobre cada entrega.

Metodologia adotada: **Spec-Driven Development**. Para cada feature de negócio (auth, projects/tasks/tags, attachments), o ciclo seguido foi:
1. **Spec** — documento em `docs/specs/<feature>.md` descrevendo casos de uso, contrato de API e regras de negócio, revisado antes de qualquer código
2. **Testes** — escritos a partir da spec, propositalmente falhando antes da implementação existir ("red")
3. **Implementação** — até os testes passarem ("green"), seguindo arquitetura em camadas (api → services → repositories → models)

Todo o histórico de commits reflete essas etapas separadamente (branches `feat/*`, com commits `docs:`, `test:`, `feat:`).

## Resumo

- **67 testes automatizados** no backend (pytest), cobrindo auth, projects,
  tasks, tags e attachments — todos escritos antes da implementação
  correspondente (ciclo SDD)
- **4 specs técnicas** em `docs/specs/` (auth, projects-tasks-tags,
  attachments), revisadas e aprovadas antes de qualquer código
- **Arquitetura em camadas** (api → services → repositories → models) com
  exceções de domínio centralizadas, aplicada de forma consistente do
  backend ao frontend
- **Aplicação em produção**, ponta a ponta: backend no Render (Docker +
  Postgres gerenciado), frontend no Vercel, storage no Cloudflare R2
- Vários bugs reais identificados e corrigidos ao longo do processo —
  detalhados nas seções abaixo, incluindo um problema de `.gitignore` que
  teria quebrado o build de um clone limpo do repositório

## Cronologia detalhada

---

### Setup do monorepo (arquitetura em camadas + infraestrutura de qualidade)
- Ferramenta: Claude Code
- Branch: `chore/backend-skeleton`
- Prompt: estrutura em camadas (api/services/repositories/models), exceções de
  domínio customizadas com handler central, SQLAlchemy 2.0 async + Alembic,
  Postgres com banco de teste isolado (taskly_test), pytest com isolamento por
  transação/rollback, ruff + mypy strict, pre-commit, CI no GitHub Actions
- O que foi gerado: esqueleto completo, incluindo teste de exemplo (/health)
  já passando, pipeline de CI configurado, README documentando a arquitetura
- Testes: validado localmente antes de considerar concluído — ruff check,
  ruff format --check, mypy strict e pytest passando, além de testar Alembic
  autogenerate e subida do Postgres com os dois bancos
- Revisão/decisão:
  - Pequena inconsistência de estilo identificada em exceptions/handlers.py
    (mistura de status.HTTP_422_UNPROCESSABLE_ENTITY com literal 422 na
    mesma lista) — ajuste pontual planejado para etapa seguinte
  - CI apresentou apenas um aviso de infraestrutura da plataforma (Node.js
    20 deprecated nos runners do GitHub Actions), sem relação com o código
    do projeto — não gerou nenhuma ação

---

### Modelagem de dados + repositories
- Ferramenta: Claude Code
- Branch: `feat/data-models`
- Prompt: 6 models SQLAlchemy async, repositories genéricos por entidade,
  migration com autogenerate, teste de integração dos relacionamentos
- Testes: teste de integração real (User→Project→Task) rodando contra o
  banco de teste isolado; validado com ruff, mypy strict e pytest antes do
  commit
- Revisão/decisão:
  - Identifiquei que o PostgreSQL não remove tipos ENUM automaticamente ao
    dropar uma tabela, e ajustei manualmente o downgrade() da migration
    para também remover o tipo task_status — validado com round-trip
    completo (downgrade → upgrade) e alembic check confirmando zero drift
    entre models e schema do banco
  - A IA identificou um bug real de test runner (fixture de engine em
    escopo de sessão rodando em event loop diferente dos testes, causando
    erro no asyncpg); validei o diagnóstico e, com minha aprovação, ela
    ajustou a configuração do pytest-asyncio para corrigir

---

### Auth — Spec (Spec-Driven Development)
- Ferramenta: Claude Code
- Branch: `feat/auth`
- Metodologia: spec escrita e revisada antes de qualquer código ou teste
  (docs/specs/auth.md)
- Decisões de segurança na spec, revisadas e aprovadas por mim:
  - Mitigação de timing attack no login (verificação de hash dummy quando
    e-mail não existe, para que o tempo de resposta não vaze essa
    informação)
  - Tratamento de race condition no registro: UNIQUE do banco como fonte
    da verdade, IntegrityError capturado e convertido em erro de domínio
    (em vez de check-then-act, que tem janela de corrida)
  - Todos os erros de autenticação (token malformado, expirado, assinatura
    inválida, ausente) retornam 401 idêntico — não vaza qual foi a causa

### Auth — Testes
- Ferramenta: Claude Code
- Branch: `feat/auth`
- 14 testes de integração cobrindo a spec (registro, login, rota
  protegida), escritos antes de qualquer código de produção
- Testes falham corretamente (14 failed por 404 — rota inexistente, não
  erro de setup/import) — "red" válido confirmado com ruff + mypy + pytest
  antes de prosseguir

### Auth — Implementação
- Ferramenta: Claude Code
- Branch: `feat/auth`
- Implementação completa seguindo a spec e fazendo os 14 testes passarem
  (16/16 no total, incluindo os testes pré-existentes de health e models,
  que continuaram intactos)
- Revisão/decisão:
  - O hash "dummy" usado para mitigar timing attack no login é
    pré-computado uma única vez no import do módulo (não a cada request)
    — evita que o próprio custo de *gerar* o hash (diferente do custo de
    *verificar*) reintroduza uma diferença de tempo mensurável entre os
    caminhos "usuário existe" e "usuário não existe"
  - Uso de HTTPBearer(auto_error=False) para que a ausência do header
    Authorization não dispare o 403 automático e genérico do FastAPI,
    mantendo consistência com o padrão de exceções de domínio do projeto
    (NotAuthenticatedError → 401)
  - Fixei o JWT_SECRET_KEY nos testes (conftest.py) para tornar os testes
    de "token expirado" e "assinatura inválida" determinísticos e
    mutuamente exclusivos

---

### Projects/Tasks/Tags — Spec
- Ferramenta: Claude Code
- Branch: `feat/projects-tasks-tags`
- Spec extensa (495 linhas) cobrindo CRUD de Project/Task/Tag, checagem de
  posse, cascades, paginação e casos de borda — revisada e aprovada antes
  de qualquer teste ou código
- Decisões de destaque, revisadas e aprovadas por mim:
  - invalid_tag_ids: operação atômica (nada persistido) quando qualquer
    tag_id é inexistente ou pertence a outro projeto; erro genérico não
    distingue os dois casos, consistente com o princípio de não vazar
    existência de recursos fora do escopo do usuário
  - Deadline exige datetime timezone-aware (rejeita naive/date-only) para
    evitar ambiguidade de fuso horário
  - A IA identificou o trade-off entre retornar as listagens como array
    puro ou como um envelope com metadados de paginação ({items, total});
    validamos juntos que um envelope completo seria prematuro para o
    volume de dados esperado (YAGNI) e optamos por manter o array puro,
    documentando que migrar para envelope futuramente seria uma mudança
    que quebra compatibilidade
  - Regra de posse → sempre 404 (nunca 403) reafirmada e aplicada de forma
    consistente com a decisão já tomada na feature de auth
  - Decisão de produto que tomei: short_description obrigatório ao criar
    task (não só title), para forçar contexto mínimo

### Projects/Tasks/Tags — Testes
- Ferramenta: Claude Code
- Branch: `feat/projects-tasks-tags`
- 32 testes de integração (11 projects + 17 tasks + 4 tags) cobrindo a
  spec, escritos antes de qualquer código de produção
- "Red" confirmado: 39 failed / 16 passed (os 16 já existentes — health,
  models, auth — continuaram intactos); nenhuma falha por erro de setup,
  import ou fixture — todas por rota inexistente (404) ou assert de status
- Revisão/decisão:
  - Fixture new_user implementada como factory (não um único usuário
    fixo), permitindo criar múltiplos usuários distintos no mesmo teste
    para validar isolamento entre contas
  - Helpers de setup (create_project_id, etc.) fazem assert com mensagem
    descritiva no próprio helper, evitando que uma falha de setup apareça
    como KeyError genérico em vez de apontar a causa real

### Projects/Tasks/Tags — Implementação
- Ferramenta: Claude Code
- Branch: `feat/projects-tasks-tags`
- Implementação completa fazendo os 39 testes passarem (55/55 no total,
  incluindo os 16 pré-existentes de health/models/auth, que continuaram
  intactos); alembic check confirmou zero drift de schema mesmo com uma
  property nova adicionada ao model Task
- Revisão/decisão:
  - A IA identificou a repetição de .strip() manual em cada schema e
    propôs um tipo reutilizável (TrimmedStr, via Pydantic BeforeValidator);
    validei a abordagem e ela foi aplicada em Project/Tag/Task
  - Identifiquei a necessidade de populate_existing ao recarregar uma task
    após substituir suas tags na mesma transação, evitando que o
    SQLAlchemy devolvesse uma versão em cache (stale) do objeto — detalhe
    sutil de ORM que passa despercebido com frequência
  - A IA propôs implementar replace_task_tags como delete+reinsert atômico
    em vez de calcular diff de adição/remoção; validei que essa abordagem
    era mais simples e igualmente segura dentro da mesma transação, e ela
    seguiu com essa implementação

---

### Attachments — Spec
- Ferramenta: Claude Code
- Branch: `feat/attachments`
- Spec cobrindo upload/remoção de anexos via Cloudflare R2, validação de
  arquivo e tratamento de falhas de storage — revisada e aprovada antes de
  qualquer teste ou código
- Decisão de arquitetura que tomei: bucket com acesso via URL pré-assinada
  e TTL configurável, para controlar de forma explícita por quanto tempo
  cada link de anexo fica acessível
- Outras decisões de destaque, revisadas e aprovadas por mim:
  - A IA identificou que validar o tipo do arquivo pelo Content-Type
    declarado pelo cliente é inseguro (pode ser forjado), e propôs validar
    pelos magic bytes reais do arquivo; validei e aprovei essa abordagem
  - Ordem objeto-primeiro-depois-registro no upload (evita registro
    órfão apontando para arquivo inexistente); ordem inversa na remoção,
    com delete do objeto no R2 como best-effort (banco é a fonte da
    verdade, uma instabilidade do R2 não trava a remoção para o usuário)
  - URL pré-assinada é montada explicitamente pelo service (módulo
    presenters.py dedicado), não injetada como contexto no schema
    Pydantic — mantém os schemas livres de dependência de infraestrutura

### Attachments — Testes
- Ferramenta: Claude Code
- Branch: `feat/attachments`
- 12 testes de integração cobrindo upload, remoção e listagem embutida no
  detalhe da task, escritos antes de qualquer código de produção
- Storage substituído por um fake em memória (tests/fake_storage.py),
  injetado via override de dependency do FastAPI — testes nunca tocam o
  R2 real, evitando lentidão e flakiness de rede
- "Red" confirmado: 12 failed / 55 passed (todos os pré-existentes
  intactos); fixture de storage protegida com guard de import para não
  quebrar a coleção dos outros arquivos de teste antes da implementação
  existir

### Attachments — Implementação
- Ferramenta: Claude Code
- Branch: `feat/attachments`
- Implementação completa fazendo os 12 testes passarem (67/67 no total);
  alembic check confirmou zero drift de schema
- Revisão/decisão:
  - sanitize_filename normaliza Unicode, remove caracteres de controle/
    separadores de path e força a extensão real detectada — proteção
    contra path traversal e nomes de arquivo maliciosos
  - A IA identificou a necessidade de remover o attachment também da
    coleção task.attachments em memória (não só do banco) antes do flush,
    para disparar o delete-orphan corretamente; validei o raciocínio e a
    correção foi aplicada
  - A IA propôs isolar a montagem de AttachmentRead/TaskRead com URL
    assinada num módulo de apresentação dedicado (presenters.py),
    mantendo services e schemas livres dessa responsabilidade cruzada;
    validei e mantive a abordagem

---

### Frontend — Setup (Vite/React/Tailwind v4/shadcn)
- Ferramenta: Claude Code
- Branch: `feat/frontend-setup`
- Metodologia: validação visual direta no navegador
- Referências visuais do Figma (protótipo com telas de login, lista,
  kanban e detalhe de tarefa) usadas para guiar a paleta de cores e
  identidade visual desde o setup inicial
- O que foi gerado: Vite + React 19 + TS, Tailwind v4 (tema via @theme em
  index.css), shadcn/ui (11 componentes), React Router com rota protegida,
  TanStack Query, client HTTP axios com interceptors de auth e tratamento
  de 401 global
- Testes: testado no navegador (automação Chrome) o redirect de rota
  protegida com/sem token e o fluxo de logout
- Revisão/decisão:
  - Definição proativa dos tokens de cor de status (neutral/progress/
    done/cancelled + variantes soft) já alinhados com a paleta da
    referência visual, antecipando as cores que os badges de status
    usariam nos próximos prompts
  - Durante o teste no navegador, identifiquei e corrigi um bug (botão
    "Sair" limpava o token mas não navegava de volta para /login)
  - Remoção dos pacotes @radix-ui/* individuais em favor do pacote
    unificado radix-ui, refletindo a mudança atual do CLI do shadcn/ui

### Frontend — Telas de autenticação
- Ferramenta: Claude Code
- Branch: `feat/frontend-auth-screens`
- Login e registro implementados seguindo a referência visual, com
  react-hook-form + zod, painel visual compartilhado extraído em
  componente próprio
- Testes: fluxo completo testado no navegador com backend real rodando
  (registro → auto-login → rota protegida → logout → senha errada →
  e-mail duplicado → validação client-side) — sem mocks, requests reais
- Bug encontrado e corrigido: o `.gitignore` da raiz (template Python
  padrão usado ao criar o repositório) tinha o padrão `lib/` sem âncora,
  que ignorava silenciosamente qualquer pasta chamada "lib" em qualquer
  nível — incluindo `frontend/src/lib/`. Ao revisar os arquivos antes de
  fazer commit e push desta etapa, percebi que `api.ts`, `auth.ts` e
  `utils.ts` não apareciam como rastreados, mesmo já existindo no
  projeto. Um clone limpo do repositório até aquele ponto quebraria o
  build por import ausente. Corrigi ancorando o padrão (`/lib/`) e
  adicionando os arquivos que estavam sendo ignorados
- Revisão/decisão:
  - Interceptor de 401 no client HTTP isenta explicitamente as rotas de
    /auth/login e /auth/register, para que um login incorreto mostre o
    erro no formulário em vez de disparar o redirect global de sessão
    expirada (que é para requisições autenticadas que falham depois de
    logado, não para a tentativa de login em si)
  - Adição de CORS no backend (CORSMiddleware com origins configuráveis),
    necessário para o frontend local se comunicar com a API

---

### Frontend — Dashboard (sidebar + lista de tarefas)
- Ferramenta: Claude Code
- Branch: `feat/frontend-dashboard`
- Sidebar de projetos, criação de projeto, visão em lista de tarefas com
  badges de status/tag, resumo de contadores, seguindo a referência
  visual do Figma
- Testes: validado no navegador com 8 tarefas semeadas via API real
  (não só o caso vazio), cobrindo empty state, criação de projeto,
  troca de projeto, abertura do detalhe da tarefa, aba Kanban placeholder

### Frontend — Kanban e criação de tarefa
- Ferramenta: Claude Code
- Branch: `feat/frontend-kanban-task`
- Visão Kanban (4 colunas por status) e formulário completo de criação
  de tarefa, incluindo multi-select de tags com criação inline
- Testes: fluxo completo testado no navegador (criar tarefa com tag nova,
  confirmar em lista e kanban, validar que a coluna do kanban bate com
  o status real) e confirmação direta do dado persistido no backend
  (deadline armazenado com timezone correta)
- Revisão/decisão:
  - A IA identificou que tags novas (ainda sem id) precisavam ser criadas
    via API antes da criação da task, resolvendo-as para UUIDs reais, para
    evitar enviar uma tag "pendente" inexistente no payload de tag_ids;
    validei a lógica e ela foi implementada assim no multi-select
  - A IA identificou que o input datetime-local do navegador não inclui
    timezone, e que isso seria rejeitado pelo backend (que exige datetime
    timezone-aware); validei e ela implementou a conversão para ISO com
    timezone via Date.toISOString() antes de enviar ao backend

### Frontend — Detalhe completo da tarefa (edição + anexos)
- Ferramenta: Claude Code
- Branch: `feat/frontend-task-detail`
- Painel de edição completo (título, descrições, status, prazo, tags) e
  seção de anexos (upload, miniatura, remoção) no Sheet de detalhe
- Testes: fluxo completo testado no navegador com upload real de arquivo
  contra um servidor S3-compatible de verdade (não mock) — todos os
  campos editados e persistência confirmada recarregando a página, não
  só verificada em estado de memória do React
- Decidi adicionar MinIO (storage S3-compatible open source) ao
  docker-compose.yml para os testes locais de upload, em vez de depender
  das credenciais reais do R2 de produção ou de um mock — permite testar
  o fluxo de upload de ponta a ponta sem tocar em infraestrutura de
  produção; validei com a IA que o storage.py já era compatível com essa
  abordagem (path-style addressing funciona tanto em MinIO quanto em R2)
- Revisão/decisão:
  - Indicador de "salvando/salvo" no cabeçalho do painel dá feedback
    visual do autosave sem exigir clique explícito em "salvar" para cada
    campo — edições de texto salvam ao perder foco, mudanças de
    status/prazo/tags salvam imediatamente
  - Mensagens de erro de upload mapeadas por status HTTP (422/413/502)
    para texto amigável específico, em vez de um erro genérico único
  - A IA identificou que manter openTask como um objeto separado em
    estado causava dessincronia com a lista após edições e remoções, e
    propôs derivá-lo da lista de tasks por id — garantindo que o Sheet
    reflita mudanças imediatamente e feche sozinho quando a task deixa
    de existir; validei e mantive essa abordagem

### Polimento final (responsividade, erros, acessibilidade, CI do frontend)
- Ferramenta: Claude Code
- Branch: `chore/polish-and-deploy`
- Job de CI para o frontend (lint + typecheck + build, paralelo ao
  backend), sidebar responsiva (rail fixo em desktop, drawer/Sheet em
  mobile), estados de erro com retry, auditoria de acessibilidade
  (labels, aria-label, foco visível), limpeza de código de debug
- Testes: validado no navegador em viewport simulado de 390px (mobile) e
  testando falha de rede de verdade (backend derrubado propositalmente)
  para confirmar que o estado de erro aparece e o retry recupera os dados
- Bug real encontrado e corrigido: queries do TanStack Query entram em
  estado "paused" (não "error") quando a rede está indisponível, e por
  padrão nada é renderizado nesse caso — a tela ficava em branco quando o
  backend caía, sem nenhuma mensagem. Corrigido com networkMode: 'always'
  e tratando isPaused como falha de carregamento na UI. Só foi descoberto
  porque testei ativamente o cenário de falha de rede, não apenas o
  caminho feliz
- Revisão/decisão:
  - Extração do conteúdo da sidebar em um componente compartilhado
    (SidebarNav) usado tanto no rail fixo desktop quanto no drawer mobile,
    evitando duplicar a lógica de listagem/seleção de projetos
  - Remoção de um probe de debug (window.__qc) esquecido no código numa
    iteração anterior de investigação — identificado na própria checagem
    de limpeza que pedi

### Preparação de deploy (Docker + Render Blueprint + Vercel)
- Ferramenta: Claude Code
- Branch: `chore/polish-and-deploy`
- Implementados: Dockerfile multi-stage de produção para o backend,
  render.yaml descrevendo a infraestrutura do Render (Blueprint), e uma
  seção de Deploy no README documentando o processo e a limitação
  conhecida do free tier
- Testes: build Docker real executado localmente contra um Postgres
  descartável — confirmou migrations aplicando no start, /health
  respondendo, processo rodando como usuário não-root, e reaplicação
  idempotente de migrations em um restart
- Bug de produção evitado: identifiquei que o Postgres gerenciado do
  Render entrega a connection string no formato genérico
  (postgres://... / postgresql://...), sem o driver assíncrono que o
  SQLAlchemy e o Alembic exigem — sem tratar isso, o deploy quebraria no
  boot de forma silenciosa. Adicionei um validador que normaliza a URL
  automaticamente para postgresql+asyncpg://, de forma idempotente
- Revisão/decisão:
  - Documentei explicitamente no README a limitação do free tier do
    Render (primeira requisição após inatividade leva 30-60s) e a
    expiração do Postgres free em 30 dias, para que quem avaliar o link
    não confunda lentidão esperada com bug
  - O Dockerfile foi configurado para rodar o processo como usuário
    não-root, seguindo boas práticas de segurança em containers de
    produção

---

## Reflexão final

Alguns padrões se repetiram ao longo do processo e valem ser destacados:

- **O ciclo Spec → Testes → Implementação funcionou como esperado**: cada
  feature de negócio teve seu comportamento especificado e testado antes
  de existir código de produção, o que tornou a implementação em si mais
  rápida e menos sujeita a retrabalho — os testes já diziam exatamente o
  que "pronto" significava.
- **Revisão ativa, não passiva**: em várias etapas, a IA identificou
  problemas ou propôs decisões técnicas que não estavam explícitas no
  prompt (bugs de ORM, trade-offs de arquitetura, detalhes de segurança).
  Nenhuma delas foi aceita automaticamente — cada uma passou por validação
  minha antes de virar código definitivo.
- **Testar de verdade importa mais do que parece**: praticamente todos os
  bugs reais encontrados (CORS, .gitignore, TanStack Query em modo
  paused) só apareceram porque a aplicação foi testada em condições
  reais — navegador de verdade, rede derrubada de propósito — não porque
  o código "parecia" estar certo na leitura.
