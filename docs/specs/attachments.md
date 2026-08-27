# Especificação — Attachments

Status: **rascunho, aguardando revisão**
Feature: upload e remoção de anexos (imagens / PDF) em uma Task, com storage
externo no Cloudflare R2 (S3-compatible)
Última atualização: 2026-08-27
Depende de: `docs/specs/auth.md`, `docs/specs/projects-tasks-tags.md`

---

## 1. Visão geral

A feature permite anexar **arquivos** (imagens ou PDF) a uma **Task existente** e
removê-los. Os bytes ficam no **Cloudflare R2** (bucket privado, S3-compatible);
o banco guarda apenas os metadados (`Attachment`).

- **Upload**: `multipart/form-data` com um arquivo → validação (tipo e tamanho) →
  `PutObject` no R2 → criação do registro `Attachment` → resposta com os
  metadados e uma **URL pré-assinada** para baixar o arquivo.
- **Remoção**: apaga o registro `Attachment` e, em *best-effort*, o objeto no R2.
- **Listagem**: **não tem endpoint próprio**. Todo `TaskRead` passa a incluir
  `attachments: list[AttachmentRead]` (§2, UC-A3).
- **Proteção por posse**: como no resto do projeto, acesso a anexo de task/projeto
  de outro usuário responde **404**, nunca 403.

### Impacto na arquitetura

Segue as camadas já estabelecidas (`api → services → repositories → models`) e o
padrão de exceções de domínio (sem `HTTPException` nos services).

| Camada | Componentes (novos/afetados) |
|---|---|
| `core/config.py` | settings do R2 + limites (`R2_*`, `ATTACHMENT_MAX_BYTES`, `ATTACHMENT_URL_TTL_SECONDS`) |
| `core/storage.py` **(novo)** | `ObjectStorage`: `put_object`, `delete_object` (async, via threadpool), `presigned_get_url` (sync, local). Cliente boto3 criado uma vez. Dependency `get_storage` (substituível nos testes). |
| `schemas/attachment.py` **(novo)** | `AttachmentRead` |
| `schemas/task.py` | `TaskRead` ganha `attachments: list[AttachmentRead]` |
| `repositories/task.py` | `get_in_project` / `list_by_project` passam a `selectinload(Task.attachments)` |
| `repositories/attachment.py` | `AttachmentRepository`: `get_in_task(task_id, attachment_id)` |
| `services/attachment_service.py` **(novo)** | regras de negócio: validação, geração de chave, orquestração storage↔banco, mapeamento de falhas para exceções de domínio |
| `api/routes/attachments.py` **(novo)** | `POST` e `DELETE` aninhados, só orquestração |
| `api/router.py` | registra o router |
| `exceptions/domain.py` | `UnsupportedFileTypeError` (→422), `FileTooLargeError` (→**413**, novo), `StorageError` (→**502**, novo) |
| `exceptions/handlers.py` | mapeia `FileTooLargeError`→413 e `StorageError`→502 |

**Sem migração de banco.** O model `Attachment` já existe (`id`, `task_id`,
`file_url`, `file_name`, `content_type`, `uploaded_at`, + `created_at` /
`updated_at`), com `task_id → tasks.id` **ON DELETE CASCADE**.

> **Nota sobre `file_url`:** a coluna guardará a **chave do objeto** no bucket
> (ex.: `attachments/<task_id>/<attachment_id>.png`), **não** uma URL pública. A
> URL apresentada ao cliente é pré-assinada e gerada na serialização (§4.3, §4.7).
> O nome da coluna é mantido por já existir.

### Dependências novas (`pyproject.toml`)

- `boto3` (traz `botocore`) — cliente S3-compatible para o R2.

### Settings novas

| Variável | Default | Descrição |
|---|---|---|
| `R2_ENDPOINT_URL` | — (obrigatória) | `https://<account_id>.r2.cloudflarestorage.com` |
| `R2_ACCESS_KEY_ID` | — (obrigatória) | credencial do token R2 |
| `R2_SECRET_ACCESS_KEY` | — (obrigatória) | credencial do token R2 |
| `R2_BUCKET` | — (obrigatória) | nome do bucket |
| `ATTACHMENT_MAX_BYTES` | `10485760` (10 MiB) | tamanho máximo do arquivo (§4.2) |
| `ATTACHMENT_URL_TTL_SECONDS` | `3600` (1 h) | validade da URL pré-assinada (§4.7) |

Como em `auth.md`, as credenciais têm de vir do ambiente; para os testes há um
`ObjectStorage` falso (§ "Testabilidade").

---

## 2. Casos de uso

Ator em todos: **usuário autenticado**. Pré-condição comum: token válido (senão
`401`, tratado pela feature de auth). Pré-condição comum das rotas aninhadas: o
**projeto `{id}` existe e pertence ao usuário** e a **task `{task_id}` existe
nesse projeto** — senão, `404` (a existência de recursos de outro usuário nunca é
revelada).

### UC-A1 — Upload de anexo em uma task

- **Pré-condições:** a task existe e é do usuário.
- **Fluxo principal:**
  1. `POST /projects/{id}/tasks/{task_id}/attachments` com `multipart/form-data`
     contendo o campo `file`.
  2. O sistema resolve projeto (posse) e task (no projeto).
  3. Lê o stream do arquivo contando os bytes; aborta se passar de
     `ATTACHMENT_MAX_BYTES` (§4.2).
  4. Determina o tipo real pelos *magic bytes* do início do arquivo (§4.1). Se
     não for um dos tipos aceitos → erro.
  5. Gera `attachment_id` (UUID) e a **chave** do objeto
     `attachments/{task_id}/{attachment_id}.{ext}` (§4.3).
  6. Faz `PutObject` no R2 sob essa chave (numa thread — §4.6).
  7. Cria o registro `Attachment` (`file_url = chave`, `file_name` =
     nome sanitizado, `content_type` = tipo detectado, `uploaded_at` = agora).
  8. Responde `201` com `AttachmentRead` (inclui a URL pré-assinada).
- **Fluxos alternativos / erro:**
  - **2a. Projeto/task não encontrados ou de outro usuário:** `404`
    `resource_not_found`. Nada é lido/enviado.
  - **3a. Sem o campo `file` no form:** `422` (shape padrão do FastAPI).
  - **3b. Arquivo maior que o limite:** `413` `file_too_large`. O upload para o
    R2 **não** é iniciado.
  - **4a. Tipo não permitido / não identificável / arquivo vazio:** `422`
    `unsupported_file_type`. Nada é enviado ao R2, nenhum registro é criado.
  - **6a. Falha no `PutObject`** (timeout, erro de rede, R2 indisponível): `502`
    `storage_error`. **Nenhum registro é criado** (§4.4).
  - **7a. A task foi apagada entre os passos 2 e 7** (race — `IntegrityError` na
    FK): o objeto recém-enviado é apagado em *best-effort* e a resposta é `404`
    `resource_not_found` (§5).

### UC-A2 — Remoção de um anexo

- **Pré-condições:** o anexo existe, numa task do usuário.
- **Fluxo principal:**
  1. `DELETE /projects/{id}/tasks/{task_id}/attachments/{attachment_id}`.
  2. O sistema resolve projeto (posse) + task (no projeto) + anexo (na task).
  3. Apaga o registro `Attachment`.
  4. Apaga o objeto no R2 em *best-effort* (§4.5): erro aqui é **logado**, não
     falha a operação.
  5. Responde `204 No Content`.
- **Fluxos alternativos / erro:**
  - **2a. Projeto/task/anexo não encontrados ou de outro usuário:** `404`
    `resource_not_found`.
  - **2b. Anexo já removido (2ª chamada):** `404` `resource_not_found` —
    consistente com a deleção de Task/Project (`projects-tasks-tags.md` UC-P5).
    O estado final continua correto ("não existe"); repetir é seguro (§5).
  - **4a. Falha ao apagar no R2:** a operação **continua** `204`. O objeto fica
    órfão e é recolhido pela reconciliação (§4.5).

### UC-A3 — Listagem de anexos (embutida no `TaskRead`)

- **Confirmação: não há endpoint de listagem de anexos.** Todo lugar que devolve
  uma task já devolve a lista completa:
  - `GET /projects/{id}/tasks` → cada item com `attachments`.
  - `GET /projects/{id}/tasks/{task_id}` → com `attachments`.
  - `POST` / `PATCH` de task → `TaskRead` com `attachments`.
  - `POST .../attachments` → devolve o `AttachmentRead` recém-criado.
- Um `GET .../attachments` seria redundante. Se no futuro a lista ficar grande a
  ponto de justificar paginação separada, aí sim se cria o endpoint; hoje não.
- **Fluxo:** `GET` da task → o repositório carrega `Task.attachments` via
  `selectinload`; cada `Attachment` vira `AttachmentRead` com uma URL
  pré-assionada fresca. Array vazio quando não há anexos.

### UC-A4 — Tentativa de upload/remoção em recurso de outro usuário

- **Ator:** usuário A, autenticado.
- **Pré-condições:** existe uma task (ou anexo) do usuário B, e A conhece/adivinha
  os ids.
- **Fluxo:**
  1. A envia `POST` ou `DELETE` com ids que pertencem a B.
  2. O sistema resolve o projeto **filtrando por `owner_id = A`**
     (`get_owned_project`); a task é buscada **dentro do projeto de A**; o anexo,
     **dentro da task**.
  3. Nada casa → `ResourceNotFoundError` → **`404`**, corpo idêntico ao de um
     recurso inexistente.
- **Observações:** nenhum `403`. No upload, o `404` acontece **antes** de
  qualquer leitura do arquivo ou chamada ao R2.

---

## 3. Contrato de API

Convenções (iguais às specs anteriores):

- Todas as rotas exigem `Authorization: Bearer <token>`; sem/ inválido → `401`
  `{ "error": { "code": "not_authenticated", ... } }`.
- Erros de validação de request (FastAPI) → `422` `{ "detail": [ ... ] }`.
- Erros de domínio → `{ "error": { "code": "<slug>", "message": "<texto>" } }`.
- `{id}` / `{task_id}` / `{attachment_id}` fora do formato UUID → `422`.
- Datas em ISO-8601 UTC.

### 3.1 Shape — `AttachmentRead`

```jsonc
{
  "id": "<uuid>",
  "file_name": "mockup-final.png",       // nome sanitizado, apenas exibição
  "content_type": "image/png",           // tipo detectado pelos magic bytes
  "uploaded_at": "2026-08-27T14:12:00Z",
  "url": "https://<account>.r2.cloudflarestorage.com/<bucket>/attachments/<task_id>/<attachment_id>.png?X-Amz-Signature=..."
  // ^ URL GET pré-assinada, válida por ATTACHMENT_URL_TTL_SECONDS
}
```

### 3.2 `TaskRead` (alteração)

Passa a incluir:

```jsonc
{
  // ... campos atuais ...
  "attachments": [ /* AttachmentRead[] */ ]
}
```

### 3.3 `POST /projects/{id}/tasks/{task_id}/attachments`

**Request:** `Content-Type: multipart/form-data`

| Campo | Tipo | Regras |
|---|---|---|
| `file` | binário (uma parte) | obrigatório; um arquivo por requisição; tipo e tamanho conforme §4.1 / §4.2 |

**Responses:**

| Status | Quando | Body |
|---|---|---|
| `201 Created` | anexo criado | `AttachmentRead` |
| `404 Not Found` | projeto/task não encontrados ou de outro usuário | `{ "error": { "code": "resource_not_found", "message": "Task not found." } }` |
| `422 Unprocessable Entity` | sem o campo `file` | shape padrão do FastAPI |
| `422 Unprocessable Entity` | tipo de arquivo não aceito / não identificável / vazio | `{ "error": { "code": "unsupported_file_type", "message": "Only JPEG, PNG, WebP and PDF files are allowed." } }` |
| `413 Content Too Large` | arquivo acima de `ATTACHMENT_MAX_BYTES` | `{ "error": { "code": "file_too_large", "message": "The file exceeds the 10 MB limit." } }` |
| `502 Bad Gateway` | falha ao enviar para o R2 | `{ "error": { "code": "storage_error", "message": "Could not store the file. Please try again." } }` |
| `401` | não autenticado | `{ "error": { "code": "not_authenticated", ... } }` |

Header opcional em `201`: `Location: /projects/{id}/tasks/{task_id}/attachments/{attachment_id}`.

### 3.4 `DELETE /projects/{id}/tasks/{task_id}/attachments/{attachment_id}`

**Request:** sem body.

**Responses:**

| Status | Quando | Body |
|---|---|---|
| `204 No Content` | anexo removido (registro apagado) | — |
| `404 Not Found` | projeto/task/anexo não encontrados ou de outro usuário; ou anexo já removido | `{ "error": { "code": "resource_not_found", "message": "Attachment not found." } }` |
| `401` | não autenticado | `{ "error": { "code": "not_authenticated", ... } }` |

Falha ao apagar o objeto no R2 **não** altera a resposta (`204`).

---

## 4. Regras de negócio

### 4.1 Tipos de arquivo aceitos

Aceitos (por *content-type* canônico):

| Tipo | Magic bytes (início) |
|---|---|
| `image/jpeg` (`.jpg`) | `FF D8 FF` |
| `image/png` (`.png`) | `89 50 4E 47 0D 0A 1A 0A` |
| `image/webp` (`.webp`) | `52 49 46 46` (`RIFF`) … `57 45 42 50` (`WEBP`) nos bytes 8–11 |
| `application/pdf` (`.pdf`) | `25 50 44 46 2D` (`%PDF-`) |

**Por quê esses:** anexos num gestor de tarefas são, na prática, *screenshots*,
mockups, fotos de recibos/documentos e PDFs de referência — os quatro formatos
cobrem quase tudo. Excluir os demais (Office, ZIP, executáveis, SVG) **reduz a
superfície de ataque**: nada de macros, *zip bombs*, HTML/JS embutido em SVG, ou
binários executáveis passando pelo bucket. WebP entra porque celulares e
navegadores já geram nesse formato e ele é eficiente.

**Como validar:** o tipo é decidido pelos **primeiros bytes do arquivo**, não
pelo `Content-Type` que o cliente declara no *multipart* nem pela extensão do
nome — ambos são controlados pelo cliente e não confiáveis. O `content_type`
**armazenado** é o detectado. A extensão da **chave** no bucket vem do tipo
detectado. Um `.png` que na verdade é um `.exe` → `422`. (Checagem via *magic
bytes* feita à mão para 4 tipos; `python-magic`/`filetype` seriam alternativas,
descartadas por trazerem dependência de sistema/pacote extra.)

### 4.2 Tamanho máximo

**10 MiB** (`ATTACHMENT_MAX_BYTES = 10 * 1024 * 1024`), configurável.

**Por quê 10 MiB:** cabe folgado uma foto de celular em alta resolução (tipicamente
2–8 MB), um PDF escaneado de várias páginas e exports de design; e é pequeno o
suficiente para o servidor bufferizar/encaminhar sem pressão de memória e para o
custo de storage/egress do R2 ficar previsível.

**Como impor (duas camadas):**

1. Se o request traz `Content-Length` e ele já excede o limite → `413` imediato,
   sem ler o corpo.
2. **Autoritativo:** ler o stream em blocos (ex. 64 KiB), somando os bytes;
   ao ultrapassar o limite, abortar → `413`. Não confiar só no `Content-Length`
   (pode faltar, ou mentir sob *chunked encoding*).

O `PutObject` no R2 só começa depois de o arquivo inteiro ter sido lido e
validado dentro do limite.

### 4.3 Nome de arquivo e colisão no bucket

- A **chave** do objeto é gerada pelo servidor:
  `attachments/{task_id}/{attachment_id}.{ext}`, onde `attachment_id` é o UUID do
  registro (gerado em Python, como todos os PKs) e `ext` vem do tipo detectado.
  → **impossível colidir** (UUID), impossível *path traversal* (nenhum caractere
  do cliente entra na chave), e os objetos ficam agrupados por task.
- O **nome original** do cliente é **sanitizado** e guardado só em
  `Attachment.file_name`, para exibição e para o `Content-Disposition` do
  download (via `ResponseContentDisposition` na URL pré-assinada). Nunca entra na
  chave. Sanitização:
  1. Se vier `None`/vazio → `"file"`.
  2. Normalizar Unicode (NFC).
  3. Remover separadores de caminho (`/`, `\`), *null bytes* e caracteres de
     controle (`0x00–0x1F`, `0x7F`).
  4. *Colapsar* espaços; remover pontos/espaços das pontas.
  5. Truncar para **200 caracteres** (preservando a extensão, se houver).
  6. Se sobrar vazio → `"file"`. Garantir a extensão correta para o tipo
     detectado.
- Nome longo ou com caracteres esquisitos **não é erro** — é sanitizado (§5).

### 4.4 Falha no upload para o R2 (registro antes ou depois?)

**Ordem: objeto primeiro, registro depois.**

1. Validar (tipo, tamanho).
2. Gerar `attachment_id` e a chave.
3. `PutObject` no R2.
4. **Se o `PutObject` falhar** (timeout, rede, R2 fora): abortar com `502`
   `storage_error`. **Nenhum registro no banco.** O `PutObject` simples (não
   *multipart*, já que o teto é 10 MiB) é atômico no S3/R2 — ou o objeto existe
   inteiro, ou não existe; não há objeto parcial para limpar.
5. Inserir o registro `Attachment` (com `flush`).
6. **Se o `flush` falhar** (ex.: a task sumiu — FK `IntegrityError`): apagar o
   objeto recém-enviado em *best-effort* e responder `404`.
7. O commit da transação acontece no fim do request (via `get_session`).

**Justificativa:** se criássemos o registro primeiro e o upload falhasse,
ficaríamos com uma linha `Attachment` apontando para um objeto inexistente —
toda serialização de `TaskRead` geraria uma URL quebrada, e limpar exigiria
reconciliação. Fazendo o upload primeiro, o pior caso é um **objeto órfão no R2**
(sem linha no banco): invisível para o usuário, custo de centavos, e recolhido
pela reconciliação (§4.5). Órfão de objeto ≫ órfão de registro.

**Janela residual:** se o request falhar entre o `flush` e o commit, a linha é
desfeita mas o objeto permanece → órfão → reconciliação. Aceito.

### 4.5 Falha ao remover o arquivo no R2

**A remoção do registro é a operação; apagar o objeto é um efeito colateral
*best-effort* que nunca falha o request.**

- `DELETE` responde `204` desde que a **linha** `Attachment` tenha sido apagada.
- A chamada `DeleteObject` no R2 vem **depois** do `delete` da linha (e é a última
  ação que pode falhar). Erro nela é **logado** (para a reconciliação), não
  propagado.

**Justificativa:** a intenção do usuário é "esse anexo não deve mais existir". A
fonte da verdade sobre existência é o banco; sem a linha, o anexo sumiu do
`TaskRead` e nenhuma URL nova é gerada. Falhar o `DELETE` inteiro porque o R2
está fora deixaria o usuário **sem conseguir remover** durante uma indisponibilidade
e o incentivaria a repetir (corrida). Objeto órfão é o mesmo mal tolerável do
§4.4.

**Reconciliação (necessária, implementação em tarefa separada):** um job
periódico lista os objetos do bucket e apaga os que **não têm linha `Attachment`
correspondente** e têm mais de 24 h. É o único mecanismo que cobre: uploads
órfãos (§4.4), deletes de objeto que falharam (§4.5) e — importante — os objetos
deixados para trás quando uma **Task ou Project é apagada** (o `ON DELETE
CASCADE` remove as linhas `Attachment`, **mas não toca no R2**).

> **Decisão em aberto:** alternativamente, os services de deleção de Task/Project
> poderiam, antes do cascade, listar e apagar os objetos R2 associados
> (*best-effort*). Recomendo **não** fazer isso agora (acopla o caminho de
> deleção ao storage, adiciona modos de falha, contraria o "um único DELETE +
> cascade" da spec de Tasks) e deixar tudo para a reconciliação. Aberto a
> revisão.

### 4.6 boto3 é síncrono — tratamento em contexto async

O `boto3`/`botocore` é bloqueante. Para não travar o *event loop* do FastAPI:

- `core/storage.py` expõe `ObjectStorage` com métodos **`async def`** que embrulham
  as chamadas bloqueantes num *worker thread*:
  `await anyio.to_thread.run_sync(functools.partial(self._client.put_object, ...))`
  (o `anyio` já é dependência transitiva do Starlette). O mesmo para
  `delete_object`.
- `presigned_get_url` **permanece síncrono** e é chamado direto: gerar URL
  pré-assinada é **assinatura local (SigV4), sem I/O de rede** — não bloqueia.
- O cliente boto3 é criado **uma única vez** (no import do módulo / *lifespan*),
  não por request (criação é cara). Clientes `botocore` são *thread-safe* para
  chamadas concorrentes; ajustar `max_pool_connections` no `botocore.config.Config`
  se a concorrência for alta. Config para R2: `region_name="auto"`,
  `signature_version="s3v4"`, `endpoint_url=settings.r2_endpoint_url`.
- **Descartado:** `aioboto3`/`aiobotocore` (cliente S3 async nativo) — dependência
  extra e API paralela para apenas duas chamadas; o *threadpool* resolve com
  menos risco.
- **Descartado:** rota como `def` síncrona (o FastAPI rodaria no threadpool) —
  impediria `await` na sessão async do banco no mesmo handler.

### 4.7 URL de download (pré-assinada)

- O bucket R2 é **privado**. `AttachmentRead.url` é uma URL **GET pré-assinada**
  (`generate_presigned_url("get_object", ...)`), válida por
  `ATTACHMENT_URL_TTL_SECONDS` (default 1 h), gerada a cada serialização.
- Parâmetros da URL: `Bucket`, `Key`, `ResponseContentType` (o `content_type`
  detectado) e `ResponseContentDisposition`
  (`attachment; filename="<file_name>"`) — o download sai com o nome original.
- **Por quê pré-assinada e não bucket público:** URLs expiram (mesmo que o
  `DeleteObject` do §4.5 falhe, a URL para de funcionar em ≤ 1 h), o bucket não
  fica exposto, e isso combina com a postura do projeto (404-não-403, erros
  genéricos). Custo: cada serialização de `TaskRead` faz N assinaturas locais
  (baratas) e a URL muda a cada leitura.

> **Decisão em aberto — como a URL chega ao schema:** `AttachmentRead` precisa do
> `ObjectStorage` para assinar. Proposta: os routers passam
> `context={"storage": storage}` para `TaskRead.model_validate(...)` /
> `AttachmentRead.model_validate(...)` (o `storage` vem da dependency
> `get_storage`); um `model_validator(mode="after")` lê `info.context["storage"]`
> e preenche `url`. O `context` do Pydantic v2 propaga para models aninhados.
> Alternativa mais simples porém menos "limpa": um singleton de módulo
> `storage` (como o `settings`). Aberto a revisão.

### 4.8 Posse → 404 (reafirmação)

Idêntico a `projects-tasks-tags.md` §4.1: projeto/task/anexo inexistente **ou** de
outro usuário → `404 resource_not_found`, sempre. Nunca `403`. Retornar `403`
confirmaria a existência do id e permitiria enumeração.

---

## 5. Casos de borda

| # | Situação | Comportamento especificado |
|---|---|---|
| B-1 | Upload de tipo não permitido (`.docx`, `.svg`, `.zip`, `.exe`, ou `.png` que é outro binário) | Detecção por *magic bytes* → não está na allowlist → `422 unsupported_file_type`. Nada enviado ao R2, nenhum registro. |
| B-2 | Arquivo maior que `ATTACHMENT_MAX_BYTES` | `413 file_too_large`. Detectado pelo contador de bytes durante a leitura (ou pelo `Content-Length`, se presente e já maior). `PutObject` não é iniciado. |
| B-3 | Requisição sem nenhum arquivo (`file` ausente) | `422` shape padrão do FastAPI (campo `file` obrigatório). |
| B-4 | Arquivo de 0 bytes | `422 unsupported_file_type` (sem bytes não há como detectar tipo). |
| B-5 | Nome de arquivo enorme (> 200 chars) ou com `../`, emojis, RTL, controle, sem extensão | **Não é erro.** Sanitizado conforme §4.3 (remove separadores/controle, NFC, trunca em 200, garante extensão). O nome **nunca** entra na chave do bucket. |
| B-6 | Remoção de um anexo já removido (2ª chamada de `DELETE`) | `404 resource_not_found`. Consistente com a 2ª deleção de Task/Project. Estado final correto ("não existe"); repetir é seguro, não corrompe nada. |
| B-7 | Remoção de anexo cuja **task já não existe** (task apagada concorrentemente → attachments some via CASCADE) | A busca da task falha primeiro → `404 resource_not_found` ("Task not found."). A linha do anexo já sumiu pelo cascade. O **objeto no R2 fica órfão** → reconciliação (§4.5). |
| B-8 | Upload enquanto a task é apagada concorrentemente | Ou a resolução da task falha (`404`), ou o `flush` do registro falha na FK (`IntegrityError`) → o objeto recém-enviado é apagado em *best-effort* → `404 resource_not_found`. |
| B-9 | `PutObject` bem-sucedido, mas o request falha antes do commit | Linha desfeita no rollback; objeto permanece → órfão → reconciliação. |
| B-10 | Duas requisições de upload simultâneas para a mesma task | Cada uma gera `attachment_id`/chave própria → dois objetos, dois registros. Sem limite de anexos por task (fora de escopo). |
| B-11 | `content_type` do *multipart* mente (diz `application/pdf`, arquivo é PNG) | Ignorado. Vale o *magic byte* → `image/png`, chave `.png`. |
| B-12 | `{attachment_id}` válido mas de **outra task** (mesmo usuário) | `AttachmentRepository.get_in_task(task_id, attachment_id)` filtra por `task_id` → não encontra → `404`. |

---

## 6. Fora de escopo

Explicitamente **não** especificado nem implementado agora:

- **Transformação / redimensionamento de imagem**, conversão de formato,
  *strip* de EXIF.
- **Geração de thumbnails / previews.**
- **Verificação de conteúdo malicioso** (antivírus, sandbox, checagem de PDF
  ativo/JS).
- **Limite de quantidade de anexos por task** (e cota de storage por
  usuário/projeto).
- **Versionamento de arquivo** (substituir o arquivo de um anexo mantendo o id).
  Para "trocar", faz-se `DELETE` + novo `POST`.
- **Endpoint de download / proxy** dos bytes pela API. O download é feito
  diretamente no R2 pela URL pré-assinada do `AttachmentRead`.
- **Endpoint dedicado de listagem** `GET .../attachments` (a lista já vem no
  `TaskRead` — UC-A3).
- **Upload direto do browser para o R2** (via `presigned PUT` / *POST policy*),
  que evitaria os bytes passarem pela API. Possível otimização futura; por ora a
  API recebe e encaminha.
- **Implementação do job de reconciliação** (§4.5). O mecanismo é especificado
  aqui como necessário; a implementação (tarefa agendada) é *follow-up*
  rastreado à parte.
- **Múltiplos arquivos numa única requisição** (`file` é uma parte só).

---

## Testabilidade (nota para a fase de testes)

- `ObjectStorage` é injetado via dependency `get_storage`; nos testes é
  substituído por um **fake em memória** que:
  - registra `put_object` / `delete_object` (para asserções),
  - devolve uma `presigned_get_url` determinística (ex.:
    `https://fake-r2.test/<key>`),
  - pode ser configurado para **falhar** (simular `502` / erro de rede) num teste
    específico.
- Nenhum teste toca o R2 real nem exige credenciais.
- Os arquivos de teste (PNG/JPEG/PDF mínimos válidos) são *fixtures* de bytes
  pequenos com os *magic bytes* corretos.
