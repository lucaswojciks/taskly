# Especificação — Projects, Tasks e Tags

Status: **rascunho, aguardando revisão**
Feature: gestão de projetos, tarefas e tags, com acesso protegido por posse
Última atualização: 2026-08-27
Depende de: `docs/specs/auth.md` (autenticação já implementada)

---

## 1. Visão geral

A feature entrega o núcleo funcional do Taskly:

- **Projects** — um usuário cria projetos; cada projeto pertence a exatamente um
  usuário (o `owner`). O usuário só enxerga e manipula os próprios projetos.
- **Tasks** — tarefas vivem **dentro de um projeto**. Campos: `title`
  (título), `short_description` (descrição curta), `full_description` (descrição
  completa), `deadline` (prazo, opcional), `status` (enum) e `tags` (associação
  N:N com as tags do mesmo projeto).
- **Tags** — rótulos **escopados por projeto**. Uma tag do projeto A não pode ser
  usada em tarefas do projeto B. Nesta fase há apenas criação e listagem de tags.

Tudo é **protegido por posse**: qualquer acesso a um projeto (ou a uma tarefa/tag
dentro dele) que não pertença ao usuário autenticado responde **404**, nunca 403
(ver §4.1).

### Impacto na arquitetura

Segue a arquitetura em camadas já estabelecida
(`api → services → repositories → models`) e o padrão de exceções de domínio
(`app/exceptions/domain.py` + handler central, sem `HTTPException` nos services).

| Camada | Componentes (novos/afetados) |
|---|---|
| `schemas/` | `project.py` (`ProjectCreate`, `ProjectUpdate`, `ProjectRead`), `task.py` (`TaskCreate`, `TaskUpdate`, `TaskRead`), `tag.py` (`TagCreate`, `TagRead`) |
| `services/` | `project_service.py`, `task_service.py`, `tag_service.py` |
| `repositories/` | `project.py`, `task.py`, `tag.py`, `task_tag.py` ganham as queries específicas (`list_by_owner`, `get_owned`, `list_by_project`, `get_in_project`, `replace_task_tags`, ...) |
| `api/routes/` | `projects.py`, `tasks.py`, `tags.py` |
| `api/router.py` | registra os três routers |
| `core/dependencies.py` | dependency `get_owned_project` (resolve `{id}` + posse → 404) reutilizada pelas rotas aninhadas |
| `exceptions/domain.py` | reutiliza `ResourceNotFoundError` (404) e `ValidationError` (422); **nenhuma exceção nova** |

**Sem migração de banco.** Os models `Project`, `Task`, `Tag`, `TaskTag` e
`Attachment` já existem (`feat(backend): core domain models`), com os cascades
`ON DELETE` já definidos.

### Modelo de dados (recapitulação — já existente)

| Model | Campos relevantes | FKs e cascata |
|---|---|---|
| `Project` | `id`, `name`, `owner_id`, `created_at`, `updated_at` | `owner_id → users.id` **ON DELETE RESTRICT** |
| `Task` | `id`, `project_id`, `title`, `short_description`, `full_description`, `deadline` (nullable), `status`, timestamps | `project_id → projects.id` **ON DELETE CASCADE** |
| `Tag` | `id`, `name`, `project_id`, timestamps | `project_id → projects.id` **ON DELETE CASCADE** |
| `TaskTag` | `id`, `task_id`, `tag_id`, timestamps | ambos **ON DELETE CASCADE**; `UNIQUE(task_id, tag_id)` |
| `Attachment` | `id`, `task_id`, `file_url`, ... | `task_id → tasks.id` **ON DELETE CASCADE** |

`status` é o enum `task_status`: `not_started` (default), `in_progress`, `done`,
`cancelled`.

---

## 2. Casos de uso

Ator em todos os casos: **usuário autenticado** (possui um access token válido —
ver `auth.md`). Pré-condição comum a todos: o token é válido; caso contrário a
resposta é `401 not_authenticated` (tratado pela feature de auth, não repetido
abaixo).

### Projects

#### UC-P1 — Criar projeto

- **Pré-condições:** nenhuma além da comum.
- **Fluxo principal:**
  1. `POST /projects` com `name`.
  2. O sistema faz trim do `name` e valida o tamanho (§4.5).
  3. O sistema cria o projeto com `owner_id = <usuário atual>`.
  4. Responde `201` com o projeto criado.
- **Fluxos alternativos / erro:**
  - **2a. `name` vazio / só espaços / acima do limite:** `422`, nenhum projeto
    criado.

#### UC-P2 — Listar os próprios projetos

- **Fluxo principal:**
  1. `GET /projects` (aceita `limit` / `offset` — §4.4).
  2. O sistema retorna **apenas** os projetos cujo `owner_id` é o usuário atual,
     ordenados por `created_at DESC, id DESC`.
  3. Responde `200` com um array (possivelmente vazio).

#### UC-P3 — Ver detalhe de um projeto

- **Fluxo principal:**
  1. `GET /projects/{id}`.
  2. O sistema carrega o projeto **filtrando por `id` e `owner_id`**.
  3. Responde `200` com o projeto.
- **Fluxos alternativos / erro:**
  - **2a. Projeto não existe OU pertence a outro usuário:** `404`
    `resource_not_found` (indistinguível — §4.1).
  - **1a. `{id}` não é um UUID válido:** `422` (validação de path do FastAPI).

#### UC-P4 — Atualizar um projeto

- **Fluxo principal:**
  1. `PATCH /projects/{id}` com os campos a alterar (`name`).
  2. O sistema resolve o projeto por `id` + `owner_id`.
  3. Aplica apenas os campos presentes no corpo, com as mesmas validações do
     create.
  4. Responde `200` com o projeto atualizado.
- **Fluxos alternativos / erro:**
  - **2a. Não encontrado / de outro usuário:** `404`.
  - **3a. `name` inválido:** `422`.
  - **1a. Corpo vazio `{}`:** `200` com o projeto inalterado (no-op permitido).

#### UC-P5 — Remover um projeto

- **Fluxo principal:**
  1. `DELETE /projects/{id}`.
  2. O sistema resolve o projeto por `id` + `owner_id`.
  3. O sistema apaga o projeto; o banco cascateia para tasks, tags e, a partir
     delas, para task_tags e attachments (§4.3).
  4. Responde `204 No Content`.
- **Fluxos alternativos / erro:**
  - **2a. Não encontrado / de outro usuário:** `404`.
  - **Idempotência:** um segundo `DELETE` do mesmo id responde `404`.

### Tasks (dentro de um Project)

Pré-condição comum às tasks: o projeto `{id}` existe **e pertence ao usuário**;
senão, todas as rotas abaixo respondem `404` (a existência do projeto de outro
usuário não é revelada).

#### UC-T1 — Criar tarefa

- **Fluxo principal:**
  1. `POST /projects/{id}/tasks` com `title`, `short_description` e,
     opcionalmente, `full_description`, `deadline`, `status`, `tag_ids`.
  2. O sistema resolve o projeto (posse).
  3. Valida os campos (§4.5). Se `tag_ids` veio, valida que **todas** existem e
     pertencem a este projeto (§4.2); deduplica ids repetidos (§5).
  4. Cria a task (status default `not_started` se omitido) e as associações de
     tag.
  5. Responde `201` com a task, incluindo a lista `tags`.
- **Fluxos alternativos / erro:**
  - **2a. Projeto não encontrado / de outro usuário:** `404`.
  - **3a. Campo inválido** (título vazio, descrição acima do limite, `deadline`
    sem timezone, `status` fora do enum): `422`.
  - **3b. `tag_ids` com id inexistente ou de outro projeto:** `422`
    `invalid_tag_ids`; **nada é criado** (operação atômica).

#### UC-T2 — Listar tarefas do projeto

- **Fluxo principal:**
  1. `GET /projects/{id}/tasks` (aceita `limit` / `offset`).
  2. O sistema resolve o projeto (posse) e retorna suas tasks, ordenadas por
     `created_at DESC, id DESC`, cada uma com suas `tags`.
  3. Responde `200` com um array (possivelmente vazio).
- **Fluxos alternativos / erro:**
  - **1a. Projeto não encontrado / de outro usuário:** `404`.

#### UC-T3 — Ver detalhe de uma tarefa

- **Fluxo principal:**
  1. `GET /projects/{id}/tasks/{task_id}`.
  2. O sistema resolve o projeto (posse) e carrega a task por `task_id` **e**
     `project_id = {id}`.
  3. Responde `200` com a task e suas `tags`.
- **Fluxos alternativos / erro:**
  - **2a. Projeto não é do usuário, OU task não existe, OU task existe mas em
    outro projeto:** `404` (todos indistinguíveis).

#### UC-T4 — Atualizar uma tarefa (campos, status e tags)

- **Fluxo principal:**
  1. `PATCH /projects/{id}/tasks/{task_id}` com qualquer subconjunto de:
     `title`, `short_description`, `full_description`, `deadline`, `status`,
     `tag_ids`.
  2. O sistema resolve projeto (posse) + task (no projeto).
  3. Aplica apenas os campos presentes:
     - `deadline: null` **limpa** o prazo; `deadline` ausente **não altera**.
     - `status`: aceita qualquer valor do enum, de qualquer estado para qualquer
       estado (não há máquina de estados — §6).
     - `tag_ids` presente: **substitui integralmente** o conjunto de tags da task
       (as que não estão na nova lista são desassociadas; a tag em si não é
       apagada). `tag_ids: []` remove todas. Ausente: tags inalteradas.
  4. Responde `200` com a task atualizada.
- **Fluxos alternativos / erro:**
  - **2a. Projeto/task não encontrados ou de outro usuário:** `404`.
  - **3a. Campo inválido:** `422`.
  - **3b. `tag_ids` com id inexistente ou de outro projeto:** `422`
    `invalid_tag_ids`; **nenhuma alteração é persistida** (atômico).

#### UC-T5 — Remover uma tarefa

- **Fluxo principal:**
  1. `DELETE /projects/{id}/tasks/{task_id}`.
  2. O sistema resolve projeto (posse) + task (no projeto).
  3. Apaga a task; o banco cascateia para `task_tags` e `attachments` dessa task
     (as tags e o projeto permanecem).
  4. Responde `204 No Content`.
- **Fluxos alternativos / erro:**
  - **2a. Não encontrado / de outro usuário:** `404`.

### Tags (dentro de um Project)

#### UC-G1 — Criar tag

- **Fluxo principal:**
  1. `POST /projects/{id}/tags` com `name`.
  2. O sistema resolve o projeto (posse), faz trim e valida o `name` (§4.5).
  3. Cria a tag com `project_id = {id}`.
  4. Responde `201` com a tag.
- **Fluxos alternativos / erro:**
  - **2a. Projeto não encontrado / de outro usuário:** `404`.
  - **2b. `name` inválido:** `422`.
  - **Nome duplicado no mesmo projeto:** permitido nesta fase (§5).

#### UC-G2 — Listar tags do projeto

- **Fluxo principal:**
  1. `GET /projects/{id}/tags` (aceita `limit` / `offset`).
  2. O sistema resolve o projeto (posse) e retorna suas tags, ordenadas por
     `created_at DESC, id DESC`.
  3. Responde `200` com um array (possivelmente vazio).
- **Fluxos alternativos / erro:**
  - **1a. Projeto não encontrado / de outro usuário:** `404`.

### Acesso cruzado entre usuários

#### UC-X1 — Tentar acessar/modificar recurso de outro usuário

- **Ator:** usuário autenticado A.
- **Pré-condições:** existe um projeto (ou task, ou tag) que pertence ao usuário
  B, e A conhece (ou adivinha) o `id`.
- **Fluxo principal (todas as rotas):**
  1. A envia a requisição (`GET`/`PATCH`/`DELETE`/`POST` aninhado) com um `id`
     que pertence a B.
  2. O sistema tenta resolver o recurso **filtrando sempre por
     `owner_id = A`** (ou, para recursos aninhados, pela posse do projeto pai).
  3. A query não retorna nada → o sistema levanta `ResourceNotFoundError`.
  4. Resposta: **`404 resource_not_found`**, corpo idêntico ao de um recurso que
     de fato não existe.
- **Observações:**
  - Nunca é retornado `403`. A distinção "existe mas não é seu" vs. "não existe"
    não é observável (§4.1).
  - Vale também para `tag_ids` em UC-T1/UC-T4: uma tag de outro projeto (mesmo
    que do próprio usuário, em outro projeto) é tratada como inválida → `422`
    genérico, sem dizer que o id existe em outro lugar.

---

## 3. Contrato de API

Convenções (iguais às de `auth.md`):

- Todas as rotas exigem `Authorization: Bearer <token>`. Sem token / inválido →
  `401 { "error": { "code": "not_authenticated", ... } }`.
- Erros de validação de request (Pydantic/FastAPI) → `422` no shape padrão do
  FastAPI: `{ "detail": [ { "loc": [...], "msg": "...", "type": "..." } ] }`.
- Erros de domínio → `{ "error": { "code": "<slug>", "message": "<texto>" } }`.
- Datas em ISO-8601 UTC (`2026-09-01T18:00:00Z`). `deadline` na entrada deve ser
  **timezone-aware**.
- Listagens retornam um **array JSON puro** (sem envelope), aceitando `limit` e
  `offset` (§4.4).
- `{id}` / `{task_id}` fora do formato UUID → `422` (validação de path).

### Shapes

```jsonc
// ProjectRead
{ "id": "<uuid>", "name": "Website", "created_at": "<iso>", "updated_at": "<iso>" }

// TagRead
{ "id": "<uuid>", "project_id": "<uuid>", "name": "urgent",
  "created_at": "<iso>", "updated_at": "<iso>" }

// TaskRead
{
  "id": "<uuid>", "project_id": "<uuid>",
  "title": "Design homepage",
  "short_description": "Mockups da home",
  "full_description": "",
  "deadline": "2026-09-01T18:00:00Z",   // ou null
  "status": "not_started",
  "tags": [ /* TagRead[] */ ],
  "created_at": "<iso>", "updated_at": "<iso>"
}
```

### 3.1 Projects

| Método / path | Request body | Responses |
|---|---|---|
| `GET /projects` | — (query: `limit`, `offset`) | `200` `ProjectRead[]` · `401` |
| `POST /projects` | `{ "name": "Website" }` | `201` `ProjectRead` · `422` · `401` |
| `GET /projects/{id}` | — | `200` `ProjectRead` · `404` · `401` |
| `PATCH /projects/{id}` | `{ "name": "Novo nome" }` (todos opcionais) | `200` `ProjectRead` · `404` · `422` · `401` |
| `DELETE /projects/{id}` | — | `204` · `404` · `401` |

`name`: string, 1–120 chars após trim.

### 3.2 Tasks

| Método / path | Request body | Responses |
|---|---|---|
| `GET /projects/{id}/tasks` | — (query: `limit`, `offset`) | `200` `TaskRead[]` · `404` · `401` |
| `POST /projects/{id}/tasks` | `TaskCreate` (abaixo) | `201` `TaskRead` · `404` · `422` · `401` |
| `GET /projects/{id}/tasks/{task_id}` | — | `200` `TaskRead` · `404` · `401` |
| `PATCH /projects/{id}/tasks/{task_id}` | `TaskUpdate` (abaixo) | `200` `TaskRead` · `404` · `422` · `401` |
| `DELETE /projects/{id}/tasks/{task_id}` | — | `204` · `404` · `401` |

```jsonc
// TaskCreate
{
  "title": "Design homepage",              // obrigatório, 1–200 após trim
  "short_description": "Mockups da home",   // obrigatório, 1–500 após trim
  "full_description": "Detalhes...",         // opcional, default "", 0–20000
  "deadline": "2026-09-01T18:00:00Z",       // opcional, nullable, aware datetime
  "status": "not_started",                   // opcional, default "not_started"
  "tag_ids": ["<uuid>", "<uuid>"]            // opcional, default []
}

// TaskUpdate  (PATCH — todos os campos opcionais; só os presentes são aplicados)
{
  "title": "...",
  "short_description": "...",
  "full_description": "...",
  "deadline": null,             // null limpa; ausente não altera
  "status": "in_progress",
  "tag_ids": ["<uuid>"]         // substitui todo o conjunto; [] remove todas; ausente não altera
}
```

**Erro de domínio específico das tasks:**

| Código | Status | Quando | Body |
|---|---|---|---|
| `invalid_tag_ids` | `422` | `tag_ids` contém id inexistente ou de outro projeto | `{ "error": { "code": "invalid_tag_ids", "message": "One or more tag_ids are invalid or do not belong to this project." } }` |

### 3.3 Tags

| Método / path | Request body | Responses |
|---|---|---|
| `GET /projects/{id}/tags` | — (query: `limit`, `offset`) | `200` `TagRead[]` · `404` · `401` |
| `POST /projects/{id}/tags` | `{ "name": "urgent" }` | `201` `TagRead` · `404` · `422` · `401` |

`name`: string, 1–50 chars após trim.

---

## 4. Regras de negócio

### 4.1 Toda checagem de posse retorna 404 (nunca 403)

Qualquer recurso (projeto, task, tag) que **não exista** ou que **exista mas
pertença a outro usuário** produz a **mesma** resposta: `404` com
`code = "resource_not_found"` e corpo genérico.

**Justificativa (reafirmando a decisão já adotada no projeto):** o Taskly já trata
sinais de existência como informação sensível — o login devolve o mesmo `401`
para "e-mail não existe" e "senha errada" (`auth.md` §4.3), e o handler de token
converge todos os modos de falha para um único `not_authenticated`. Retornar
`403` para um recurso de outro usuário **confirmaria que aquele `id` existe**,
permitindo que um atacante enumere ids de projetos/tarefas alheios apenas
observando `403` vs `404`. Com `404` uniforme, "não é seu" e "não existe" são
indistinguíveis. A exceção `PermissionDeniedError` (→ 403) permanece no código
reservada para um cenário futuro de **permissões dentro de um recurso que o
usuário comprovadamente enxerga** (ex.: projeto compartilhado com papéis), que
não é o caso aqui.

### 4.2 `tag_ids` inválidos ao criar/atualizar Task

Quando o corpo traz `tag_ids`, o service carrega as tags correspondentes
**filtrando por `project_id` do projeto da task**. A operação só prossegue se
`tags_encontradas == set(tag_ids_deduplicados)`. Caso contrário:

- Resposta `422`, `code = "invalid_tag_ids"`.
- **Nada é persistido** — nem a task (no create), nem qualquer campo (no update).
  A operação é atômica.
- Um id **inexistente** e um id **de outro projeto** (inclusive de outro projeto
  do próprio usuário) são reportados **da mesma forma**, sem dizer qual é qual —
  consistente com §4.1 (não confirmar existência de recursos fora do escopo
  atual).
- Ids repetidos na lista são deduplicados antes da checagem e da persistência
  (§5), não são erro.

### 4.3 Deleção de Project / Task e os cascades

A deleção se apoia **inteiramente** nos `ON DELETE CASCADE` já definidos nos
models (as relationships têm `passive_deletes=True`, então o ORM não carrega os
filhos linha a linha — emite um único `DELETE` e deixa o Postgres cascatear):

- `DELETE /projects/{id}` → apaga a linha em `projects`. O banco cascateia:
  - `tasks` com aquele `project_id` (FK CASCADE) →
    - `task_tags` de cada task (FK CASCADE)
    - `attachments` de cada task (FK CASCADE)
  - `tags` com aquele `project_id` (FK CASCADE) →
    - `task_tags` de cada tag (FK CASCADE)
  - Resultado: projeto e **todos** os descendentes somem em uma transação.
- `DELETE /projects/{id}/tasks/{task_id}` → apaga a task; cascateia para
  `task_tags` e `attachments` **dessa** task. Tags e projeto permanecem.
- `Project.owner_id → users.id` é **ON DELETE RESTRICT**, mas isso não afeta
  estas rotas (nunca apagamos usuários aqui); só significa que apagar um usuário
  exige apagar os projetos dele antes.
- **Arquivos físicos dos attachments** (no storage de objetos) **não** são
  removidos por esta feature — apenas as linhas do banco. A limpeza do storage é
  responsabilidade da feature de Attachments (fora de escopo — §6).

### 4.4 Paginação

**É necessária agora?** Não de forma completa. O Taskly é um gestor de tarefas
pessoal: a contagem de projetos/tarefas/tags de um único usuário fica na casa de
dezenas a poucas centenas. Cursor, contagem total e envelope de metadados seriam
prematuros (YAGNI).

**Padrão adotado para todos os list endpoints:**

- Query params `limit` (default **50**, máximo **200**, mínimo 1) e `offset`
  (default **0**, mínimo 0). Valores fora da faixa → `422`.
- Ordenação **determinística**: `created_at DESC, id DESC` (o `id` como
  desempate garante ordem estável entre páginas).
- A resposta é um **array JSON puro**, sem envelope.

**Justificativa e trade-off:** é barato de implementar, impede respostas
ilimitadas patológicas, e a query (`ORDER BY ... LIMIT ? OFFSET ?`) evolui sem
retrabalho para uma paginação mais rica. O custo assumido é que **passar a
devolver um envelope** (`{ "items": [...], "total": N }`) no futuro seria uma
mudança **quebra-contrato**; aceitamos isso agora em nome da simplicidade e
revisamos se/quando surgir um caso real de coleções grandes.

### 4.5 Validação de campos

Trim (`.strip()`) é aplicado a `name`/`title`/`short_description` **antes** da
verificação de tamanho, então " " vira "" e falha o mínimo.

| Campo | Regra |
|---|---|
| `Project.name` | string, **1–120** chars após trim |
| `Tag.name` | string, **1–50** chars após trim |
| `Task.title` | string, **1–200** chars após trim |
| `Task.short_description` | string, **1–500** chars após trim |
| `Task.full_description` | string, **0–20000** chars (pode ser vazia; sem trim de conteúdo) |
| `Task.deadline` | ISO-8601 **datetime com timezone**; naive (sem tz) → `422`; armazenado como UTC; **pode estar no passado** (§5) |
| `Task.status` | um valor do enum `task_status`; qualquer outro → `422` |
| `tag_ids` | lista de UUIDs; formato inválido → `422`; semântica em §4.2 |

Limites escolhidos por serem folgados para uso real e ainda protegerem contra
payloads abusivos. `full_description` em `Text` no banco suporta mais que 20000,
mas o limite de API evita documentos gigantes via essa rota.

---

## 5. Casos de borda

| # | Situação | Comportamento especificado |
|---|---|---|
| B-1 | `name` / `title` vazio ou só espaços | Trim → string vazia → falha `min_length=1` → `422`. Nunca cria "" no banco. |
| B-2 | `deadline` no passado (ex.: registrar tarefa atrasada retroativamente) | **Permitido**, tanto no create quanto no update. Não há regra "prazo deve ser futuro" — logar uma tarefa já vencida é caso de uso legítimo. Uma UI pode alertar visualmente; a API não bloqueia. |
| B-3 | Remover uma tag associada a várias tasks | **Não há endpoint de deleção de tag nesta fase** (só `POST`/`GET`). Remover a *associação* de uma task específica se faz via `PATCH task` com `tag_ids` sem aquela tag — isso não afeta as outras tasks nem apaga a tag. Se/quando um `DELETE /projects/{id}/tags/{tag_id}` for adicionado, a FK `task_tags.tag_id` **ON DELETE CASCADE** removeria automaticamente a tag de todas as tasks; as tasks em si ficam intactas. |
| B-4 | `tag_ids` com ids duplicados na mesma lista (`["a","a","b"]`) | **Deduplicado silenciosamente** para `{"a","b"}` antes de validar e persistir. Não é erro. O `UNIQUE(task_id, tag_id)` do banco reforça isso como rede de segurança. A resposta reflete o conjunto deduplicado. |
| B-5 | Nome de projeto duplicado para o mesmo usuário | **Permitido.** Não há constraint `UNIQUE(owner_id, name)` no model. Nome de projeto é um rótulo, não um identificador — um usuário pode legitimamente ter dois "Pessoal" ou dois "Inbox". O `id` (UUID) é a identidade. |
| B-6 | Nome de tag duplicado no mesmo projeto | **Permitido** nesta fase (o model não tem `UNIQUE(project_id, name)`). Registrado como candidato a constraint futura, mas não bloqueia agora. |
| B-7 | `PATCH` com corpo `{}` (nenhum campo) | `200` com o recurso inalterado (no-op). `updated_at` **não** muda se nada foi alterado. |
| B-8 | `PATCH task` com `tag_ids` igual ao conjunto atual | Idempotente: recalcula as associações para o mesmo conjunto, `200`. |
| B-9 | Criar task em projeto vazio de tags, passando `tag_ids: []` | OK — task criada sem tags. |
| B-10 | `GET` de lista quando não há nada | `200 []` (array vazio, nunca `404`). |
| B-11 | `deadline` enviado como data sem horário (`2026-09-01`) | `422` — exigimos datetime completo com timezone para evitar ambiguidade de fuso/hora. |
| B-12 | `offset` além do total de registros | `200 []`. |

---

## 6. Fora de escopo

Explicitamente **não** especificado nem implementado agora:

- **Reordenação / drag-and-drop de tarefas.** É comportamento de UI; não há campo
  `position`/`order` nem endpoint de reordenação. O cliente ordena como quiser na
  exibição; a API entrega ordenado por data de criação.
- **Notificações / lembretes** (por prazo, por atribuição, e-mail, push).
- **Tarefas recorrentes** (repetição por regra de recorrência).
- **Subtarefas / hierarquia de tarefas** (checklists dentro de uma task,
  dependências entre tasks).
- **API de Attachments** (upload, download, listagem, remoção de anexos e limpeza
  do storage). Só o comportamento de **cascade na deleção** (§4.3) é considerado
  aqui.
- **Deleção e edição de Tags** (`DELETE`/`PATCH` em tags) — nesta fase só
  `POST`/`GET`.
- **Filtro/busca de tasks** por `status`, por tag, por texto, por intervalo de
  prazo. Extensão natural, mas não agora.
- **Compartilhamento de projetos / colaboração** (múltiplos donos, papéis,
  convites) — e, por consequência, uso de `PermissionDeniedError`/403.
- **Operações em lote** (criar/atualizar/remover várias tasks numa requisição).
- **Locking otimista / controle de concorrência** (ex.: `If-Match`/`version`).
  `updated_at` é apenas informativo.
- **Envelope de paginação com contagem total** (ver trade-off em §4.4).
