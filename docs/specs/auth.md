# Especificação — Autenticação

Status: **rascunho, aguardando revisão**
Feature: registro e login com e-mail/senha, sessão via JWT
Última atualização: 2026-08-27

---

## 1. Visão geral

A feature de autenticação entrega:

- **Registro** de um novo usuário com e-mail e senha.
- **Login** com e-mail e senha, devolvendo um **JWT de acesso** (stateless, sem
  sessão no servidor).
- **Identificação do usuário autenticado**: um endpoint que devolve os dados do
  próprio usuário a partir do token.
- Um mecanismo reutilizável de **proteção de rotas** (dependency que valida o
  token e injeta o usuário atual), que as próximas features (projetos, tarefas,
  etc.) vão consumir.

O token é um JWT assinado com algoritmo simétrico (HS256) e chave secreta da
aplicação. Não há refresh token, logout no servidor nem blacklist nesta fase: o
token é válido até expirar.

### Impacto na arquitetura

Segue a arquitetura em camadas já estabelecida. Componentes afetados/criados:

| Camada | Componente | Responsabilidade |
|---|---|---|
| `core/config.py` | novas settings | `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` |
| `core/security.py` | funções puras | hash/verificação de senha, encode/decode de JWT |
| `core/dependencies.py` | `get_current_user` | extrai e valida o Bearer token, carrega o usuário |
| `schemas/auth.py` | Pydantic | `RegisterRequest`, `LoginRequest`, `TokenResponse`, `UserResponse` |
| `services/auth_service.py` | regras de negócio | `register(...)`, `authenticate(...)` |
| `repositories/user.py` | queries | já possui `get_by_email` e `create` |
| `api/routes/auth.py` | routers | `POST /auth/register`, `POST /auth/login`, `GET /auth/me` |
| `exceptions/domain.py` | exceções de domínio | `InvalidCredentialsError`, `NotAuthenticatedError` |
| `exceptions/handlers.py` | mapeamento | ambas as exceções acima → HTTP 401 |

**Sem migração de banco.** O model `User` já tem `email` (único, indexado) e
`hashed_password`. Nenhuma coluna nova é necessária.

### Dependências novas (a adicionar no `pyproject.toml`)

- `pyjwt` — encode/decode de JWT. Biblioteca mantida e amplamente usada; evita o
  `python-jose`, que tem histórico de problemas de manutenção/segurança.
- `pwdlib[bcrypt]` — interface de hashing de senha com backend bcrypt. É a
  abstração recomendada atualmente pela documentação do FastAPI (sucessora do
  `passlib`, que está sem manutenção ativa) e facilita trocar de algoritmo no
  futuro sem mexer nos services.

---

## 2. Casos de uso

### UC-1 — Registro de novo usuário

- **Ator:** visitante não autenticado.
- **Pré-condições:** nenhuma.
- **Fluxo principal:**
  1. O ator envia `POST /auth/register` com `email` e `password`.
  2. O sistema normaliza o e-mail (trim + lowercase — ver §5).
  3. O sistema valida o formato do e-mail e os requisitos de senha (§4).
  4. O sistema verifica que não existe usuário com aquele e-mail.
  5. O sistema gera o hash da senha (bcrypt) e persiste o novo usuário.
  6. O sistema responde `201 Created` com `id`, `email` e `created_at`.
- **Fluxos alternativos / erro:**
  - **3a. Corpo inválido** (campo ausente, e-mail malformado, senha curta):
    responde `422` com o shape padrão de validação do FastAPI. Nenhum usuário é
    criado.
  - **4a. E-mail já cadastrado:** responde `409 Conflict` com
    `code = "email_already_exists"`. Nenhum usuário é criado.
  - **5a. Registro concorrente com o mesmo e-mail** (dois requests passam pelo
    passo 4 simultaneamente): a `UNIQUE` constraint do banco rejeita o segundo
    `INSERT`; o service captura o `IntegrityError` e converte em
    `EmailAlreadyExistsError` → `409` (mesma resposta do 4a). Ver §5.

> **Decisão em aberto:** o registro **não** faz login automático nem devolve
> token; o usuário precisa chamar `POST /auth/login` em seguida. Alternativa
> considerada: devolver o token já no `201`. Mantido separado para deixar os
> fluxos independentes e o contrato de cada endpoint simples.

### UC-2 — Login

- **Ator:** usuário registrado, não autenticado.
- **Pré-condições:** existe um usuário com o e-mail informado.
- **Fluxo principal:**
  1. O ator envia `POST /auth/login` com `email` e `password`.
  2. O sistema normaliza o e-mail e busca o usuário.
  3. O sistema verifica a senha contra o hash armazenado.
  4. O sistema emite um JWT de acesso com `sub = <user id>`, `iat`, `exp` e
     `type = "access"`.
  5. O sistema responde `200 OK` com `access_token`, `token_type = "bearer"` e
     `expires_in` (segundos).
- **Fluxos alternativos / erro:**
  - **2a. E-mail não encontrado** *ou* **3a. senha incorreta:** respondem a
    **mesma** resposta genérica `401 Unauthorized` com
    `code = "invalid_credentials"` e mensagem `"Invalid email or password."`
    (§4). Para não vazar por timing, quando o e-mail não existe o sistema ainda
    executa uma verificação de hash "dummy" antes de responder.
  - **1a. Corpo inválido:** `422` (shape padrão do FastAPI).

### UC-3 — Consulta dos próprios dados

- **Ator:** usuário autenticado.
- **Pré-condições:** o ator possui um token de acesso válido e não expirado.
- **Fluxo principal:**
  1. O ator envia `GET /auth/me` com header `Authorization: Bearer <token>`.
  2. O sistema valida a assinatura e a expiração do token.
  3. O sistema lê o claim `sub`, carrega o usuário correspondente.
  4. O sistema responde `200 OK` com `id`, `email` e `created_at`.
- **Fluxos alternativos / erro:**
  - **2a / 3a. Token ausente, malformado, assinatura inválida, expirado, ou
    `sub` referencia um usuário inexistente:** responde `401 Unauthorized` com
    `code = "not_authenticated"` e mensagem genérica (§5).

### UC-4 — Acesso a rota protegida sem token / token inválido / token expirado

Aplica-se a **qualquer** rota protegida (o `GET /auth/me` é o primeiro exemplo;
projetos e tarefas virão depois).

- **Ator:** cliente da API.
- **Pré-condições:** a rota exige autenticação.
- **Fluxos:**
  - **Sem token** (header `Authorization` ausente ou com esquema diferente de
    `Bearer`): `401` com `code = "not_authenticated"`.
  - **Token malformado** (não é um JWT com 3 partes / base64 inválido): `401`,
    mesma resposta.
  - **Assinatura inválida** (token adulterado ou assinado com outra chave):
    `401`, mesma resposta.
  - **Token expirado** (`exp` no passado): `401`, mesma resposta.
  - **Token com `type` diferente de `"access"`:** `401`, mesma resposta.
  - Em todos os casos o corpo é idêntico; a causa específica pode ser registrada
    em log de nível `debug`, nunca devolvida ao cliente. Ver §5.
  - Opcionalmente o response inclui o header `WWW-Authenticate: Bearer`.

---

## 3. Contrato de API

Convenções de erro:

- **Erros de validação de request** (Pydantic/FastAPI) → `422` com o shape padrão
  do FastAPI: `{"detail": [{"loc": [...], "msg": "...", "type": "..."}]}`.
- **Erros de domínio** → envelope padrão do projeto:
  `{"error": {"code": "<slug>", "message": "<texto>"}}`.
- Datas em ISO-8601 UTC (`2026-08-27T12:00:00Z`).

### 3.1 `POST /auth/register`

**Request body** (`application/json`):

```json
{
  "email": "user@example.com",
  "password": "correct horse battery"
}
```

| Campo | Tipo | Regras |
|---|---|---|
| `email` | string | formato de e-mail válido; normalizado (trim + lowercase) |
| `password` | string | 8 a 72 caracteres (§4) |

**Responses:**

| Status | Quando | Body |
|---|---|---|
| `201 Created` | usuário criado | `{ "id": "<uuid>", "email": "user@example.com", "created_at": "<iso8601>" }` |
| `409 Conflict` | e-mail já existe (inclui race condition) | `{ "error": { "code": "email_already_exists", "message": "A user with this email already exists." } }` |
| `422 Unprocessable Entity` | corpo inválido (campo ausente, e-mail malformado, senha fora do tamanho) | shape padrão do FastAPI |

`hashed_password` **nunca** aparece em nenhuma response.

### 3.2 `POST /auth/login`

**Request body** (`application/json`):

```json
{
  "email": "user@example.com",
  "password": "correct horse battery"
}
```

**Responses:**

| Status | Quando | Body |
|---|---|---|
| `200 OK` | credenciais válidas | `{ "access_token": "<jwt>", "token_type": "bearer", "expires_in": 3600 }` |
| `401 Unauthorized` | e-mail não existe **ou** senha incorreta | `{ "error": { "code": "invalid_credentials", "message": "Invalid email or password." } }` |
| `422 Unprocessable Entity` | corpo inválido | shape padrão do FastAPI |

Observações:

- O corpo é **JSON**, não `application/x-www-form-urlencoded`. (Isso significa
  que o botão "Authorize" do Swagger UI, que usa o form OAuth2, não funciona
  direto; aceitável nesta fase.)
- `expires_in` é redundante com o `exp` do token, mas evita que o cliente tenha
  que decodificar o JWT para saber quando renovar.

### 3.3 `GET /auth/me`

**Request:** sem body. Header obrigatório:

```
Authorization: Bearer <jwt>
```

**Responses:**

| Status | Quando | Body |
|---|---|---|
| `200 OK` | token válido, usuário existe | `{ "id": "<uuid>", "email": "user@example.com", "created_at": "<iso8601>" }` |
| `401 Unauthorized` | token ausente / malformado / assinatura inválida / expirado / `type` errado / usuário inexistente | `{ "error": { "code": "not_authenticated", "message": "Not authenticated." } }` |

---

## 4. Regras de negócio

### 4.1 Unicidade de e-mail

O e-mail é único entre todos os usuários, comparado **após normalização**
(trim + lowercase). A fonte da verdade é a constraint `UNIQUE` +
índice de `users.email`.

- O service faz uma checagem "olhe antes de inserir" (`get_by_email`) como
  caminho rápido, devolvendo `409 / email_already_exists` quando encontra.
- Mesmo assim, o `INSERT` pode falhar por `IntegrityError` (race condition — §5);
  nesse caso o service traduz para `EmailAlreadyExistsError`, resultando na
  **mesma** resposta `409`.

### 4.2 Requisitos de senha

- **Mínimo: 8 caracteres.**
- **Máximo: 72 caracteres.** O bcrypt opera apenas sobre os primeiros 72 bytes
  da entrada; impor o limite evita truncamento silencioso e comportamento
  surpreendente.
- **Sem regras de composição** (não exigimos número/maiúscula/símbolo). Segue a
  orientação do NIST SP 800-63B: comprimento e ausência de senhas triviais
  protegem mais que regras de composição, que empurram usuários para padrões
  previsíveis.
- Verificação contra listas de senhas vazadas / senhas comuns fica **fora de
  escopo** nesta fase (§6).
- A senha nunca é logada nem retornada.

### 4.3 Mensagens de erro de login

Falha de login por **e-mail inexistente** e por **senha incorreta** produzem
resposta **idêntica**: `401`, `code = "invalid_credentials"`,
`message = "Invalid email or password."`. Isso impede *user enumeration* pela
API.

Mitigação de enumeração por *timing*: quando o e-mail não existe, o sistema
executa uma verificação de hash contra um hash bcrypt fixo ("dummy") antes de
responder, para que o tempo de resposta seja comparável ao de uma senha errada.

### 4.4 Expiração do token

- **Access token: 60 minutos** (`ACCESS_TOKEN_EXPIRE_MINUTES = 60`), configurável
  por ambiente.
- **Justificativa:** como não há refresh token nesta fase, o access token é a
  única credencial de sessão. Um valor muito curto forçaria re-login constante
  (ruim para um app de tarefas de uso contínuo); um valor muito longo aumenta a
  janela de risco se o token vazar. 60 minutos é um meio-termo comum e o valor é
  configurável para que operações possam apertar se necessário.
- Quando o refresh token entrar (fora de escopo — §6), o access token deve cair
  para ~15 minutos.
- Sem tolerância de *clock skew* por padrão (`leeway = 0`). Um `exp` no passado,
  por qualquer margem, é expirado.

### 4.5 Hash de senha

- **Algoritmo: bcrypt**, com *cost factor* **12**.
- **Por quê:**
  - *Custo adaptável*: o *cost factor* pode ser elevado conforme o hardware
    evolui, sem mudar o esquema.
  - *Salt por hash*: embutido no próprio hash; não precisamos gerenciar salts.
  - *Maduro e onipresente*: implementação de referência estável, ampla revisão,
    suporte em toda linguagem — bom para um sistema que pode ter integrações.
  - Mais resistente a *brute force* em GPU do que PBKDF2.
- **Alternativa considerada:** argon2id (vencedor do Password Hashing
  Competition, *memory-hard*, melhor contra ataques com hardware dedicado).
  É uma escolha igualmente defensável; ficamos com bcrypt pela simplicidade e
  ubiquidade. A camada `core/security.py` + `pwdlib` isola o algoritmo, então a
  migração para argon2id depois é local e barata (com re-hash no próximo login).
- O identificador do algoritmo e o *cost* ficam embutidos no hash armazenado em
  `users.hashed_password`, permitindo *upgrade* transparente no futuro.

### 4.6 Formato e claims do JWT

- Algoritmo: **HS256**, chave `JWT_SECRET_KEY` (obrigatória, sem default em
  produção; mínimo recomendado de 32 bytes aleatórios).
- Claims:
  - `sub` — id do usuário (UUID em string).
  - `iat` — emissão (timestamp Unix).
  - `exp` — expiração (timestamp Unix).
  - `type` — `"access"` (barreira contra reuso de outros tipos de token que
    venham a existir).
- Não colocamos e-mail nem dados sensíveis no payload (é apenas base64, não
  criptografado).

---

## 5. Casos de borda

| # | Situação | Comportamento especificado |
|---|---|---|
| B-1 | E-mail com maiúsculas/minúsculas misturadas (`User@Example.COM`) | **Normalizar para lowercase** antes de validar, buscar e persistir. `User@Example.COM` e `user@example.com` são o mesmo usuário. |
| B-2 | Espaços em branco no e-mail | **Trim** de espaços no início/fim antes de tudo. Espaços internos tornam o e-mail inválido (o validador de e-mail rejeita) → `422`. |
| B-3 | Registro concorrente com o mesmo e-mail (race condition) | A checagem prévia `get_by_email` não é suficiente sob concorrência. A `UNIQUE` constraint do banco é a fonte da verdade: o segundo `INSERT` falha com `IntegrityError`, o service captura e converte em `EmailAlreadyExistsError` → `409` (idêntico ao caso normal de e-mail duplicado). |
| B-4 | Token malformado vs. expirado vs. assinatura inválida | **Todos retornam a mesma resposta genérica** `401 / not_authenticated`, mesmo corpo. Não revelamos ao cliente qual foi o problema. A causa específica pode ir para log `debug` no servidor. |
| B-5 | Token válido na assinatura, mas `sub` não é UUID / usuário foi deletado | `401 / not_authenticated` (tratado como token inválido). |
| B-6 | Header `Authorization` presente mas com esquema errado (`Basic`, `token`, vazio) | `401 / not_authenticated`. |
| B-7 | Senha com exatamente 8 ou 72 caracteres | Aceita (limites inclusivos). 7 caracteres ou 73+ → `422`. |
| B-8 | E-mail muito longo | Limite de 320 caracteres (já é o tamanho da coluna). Acima disso → `422`. |
| B-9 | `password` só com espaços | Não há trim na senha; " " * 8 é tecnicamente válido em tamanho. Não bloqueamos (fora de escopo checar senhas triviais). |
| B-10 | Chamar `/auth/register` ou `/auth/login` já autenticado (com token) | O token é ignorado; os endpoints são públicos e se comportam normalmente. |

---

## 6. Fora de escopo desta feature

Explicitamente **não** especificado nem implementado agora:

- **Recuperação de senha** ("esqueci minha senha", envio de e-mail com link/token
  de reset).
- **Verificação de e-mail** (confirmação de endereço antes de ativar a conta).
- **OAuth / login social** (Google, GitHub, etc.).
- **Refresh token** e rotação de tokens; logout no servidor, blacklist/revogação
  de tokens, sessões múltiplas.
- **Rate limiting / proteção contra brute force** no login (recomendado, mas será
  tratado em infraestrutura/feature própria).
- **Verificação de senha contra listas de vazamento** (ex.: HaveIBeenPwned) e
  regras anti senha-trivial.
- **Papéis / permissões / autorização** além de "está autenticado" (RBAC virá com
  as features de projeto/tarefa, se necessário).
- **Auditoria** de eventos de login.
