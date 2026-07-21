---
description: "Cria hierarquia Jira a partir do spec.md e tasks.md com ACs completos e transição automática de stories"
tools:
  - '{mcp_server}/jira_create_issue'
  - '{mcp_server}/jira_update_issue'
  - '{mcp_server}/jira_search'
  - '{mcp_server}/jira_get_issue'
  - '{mcp_server}/jira_get_transitions'
  - '{mcp_server}/jira_transition_issue'
  - '{mcp_server}/jira_create_issue_link'
---

# Criar Hierarquia Jira com Critérios de Aceite

Este comando cria Epic → Stories → Sub-tasks no Jira usando conteúdo rico do spec.md.
Diferentemente da extensão jira padrão, extrai os critérios de aceite INVEST de cada
User Story do spec.md e os usa como descrição das Stories. Após criar cada Story, executa
a sequência de transições configurada em `workflow.story_creation_transitions`.

## Pré-requisitos

1. MCP server `mcp-atlassian` configurado e rodando
2. `.specify/extensions/porto/porto-config.yml` existe e está configurado
3. `specs/<spec-name>/spec.md` e `specs/<spec-name>/tasks.md` existem

## User Input

$ARGUMENTS

Aceita argumento opcional `--spec <nome>` para especificar qual spec usar.

## Steps

### 1. Detectar spec e carregar configuração

Detectar spec na seguinte ordem de prioridade:
1. Argumento `--spec <nome>` passado pelo usuário
2. Nome do branch git atual (`git branch --show-current`)
3. Nome do diretório atual
4. Único spec disponível em `specs/`

Carregar `.specify/extensions/porto/porto-config.yml`. Se não encontrar,
exibir erro informando o caminho esperado e encerrar.

Extrair as variáveis:
- `mcp_server` (ex: "mcp-atlassian")
- `project.key` (ex: "CMEI")
- `hierarchy.*` (tipos de issue e relacionamentos)
- `defaults.*` (labels por nível)
- `workflow.story_creation_transitions` (sequência de transições)
- `workflow.fallback_to_sequence`

### 2. Parse do spec.md extraindo User Stories completas

Ler `specs/<spec-name>/spec.md` e extrair cada User Story com todo seu conteúdo.

Para cada seção de User Story no spec.md, capturar:
- **Título** da User Story (ex: "US-01: Autenticação de Usuário")
- **Contexto / Narrativa**: Como [role], quero [ação], para [objetivo]
- **Critérios de aceite**: lista em formato INVEST (cada critério prefixado com AC-N)
- **Regras de negócio**: regras extraídas da seção correspondente (se houver)
- **Definição de pronto (DoD)**: critérios de conclusão (se houver)

Montar mapa interno:
```
{
  "US-01": {
    "titulo": "...",
    "narrativa": "Como ..., quero ..., para ...",
    "criterios": ["AC-1: ...", "AC-2: ..."],
    "regras": ["RN-1: ...", "RN-2: ..."],
    "dod": ["..."]
  }
}
```

**Estratégia de correspondência Phase → User Story:**
- Se Phase N existir e US-N existir → usar US-N
- Se título da Phase contém palavras-chave do título da US → usar essa US
- Caso contrário → usar a N-ésima User Story na ordem de aparecimento

### 3. Parse do tasks.md extraindo fases e tasks

Ler `specs/<spec-name>/tasks.md` e extrair:
- Phases (`## Phase N: <título>`)
- Tasks por fase com ID, descrição e status atual (`[ ]`, `[x]`, `[~]`)

Estrutura esperada:
```
## Phase 1: <título da story>
- [ ] T001: Descrição da task
- [x] T002: Descrição da task
- [~] T003: Descrição da task
```

### 4. Verificar mapping existente

Checar se `specs/<spec-name>/jira-mapping.json` existe.

Se existir, perguntar ao usuário:
- **[S] Pular existentes** — criar apenas issues faltantes (recomendado)
- **[R] Recriar tudo** — gera duplicatas no Jira, usar com cautela
- **[A] Abortar** — encerrar sem fazer nada

Se o usuário escolher Abortar, encerrar imediatamente.

### 5. Criar Epic a partir do spec.md

**Reaproveitar Epic existente**: se `jira-mapping.json` já existir e contiver
`epic.key` (por exemplo, criado previamente via `speckit.porto.epic`), reaproveitar
esse key como `epic_key` em vez de criar um novo Epic — evita duplicação quando o
épico já foi materializado antes do plan. Exibir: `↪️  Reaproveitando Epic existente: CMEI-100`.

Caso contrário, criar o Epic usando `jira_create_issue`:
- `project_key`: `project.key` da config
- `issue_type`: `hierarchy.epic_type` (ex: "Epic")
- `summary`: título principal do spec.md (primeira linha H1)
- `description`: conteúdo completo do spec.md formatado em Markdown
- `labels`: `defaults.epic.labels`
- Campos customizados de `defaults.epic.custom_fields` (se houver)

Salvar o key retornado (ex: "CMEI-100") como `epic_key`.

Exibir: `✅ Epic criado: CMEI-100 — <título>`

### 6. Para cada Phase: criar Story com descrição rica

Para cada Phase N do tasks.md:

**6.1. Montar descrição da Story**

Combinar conteúdo da User Story correspondente (do passo 2) com a lista de tasks:

```markdown
## Contexto

{narrativa da user story: "Como [role], quero [ação], para [objetivo]"}

## Critérios de Aceite

{lista de critérios de aceite do spec.md em formato INVEST}
- AC-1: ...
- AC-2: ...

## Regras de Negócio

{regras extraídas do spec.md — omitir seção se não houver}
- RN-1: ...

## Definição de Pronto

{DoD do spec.md — omitir seção se não houver}
- ...

## Tasks de Implementação

{lista de tasks da fase do tasks.md}
- T001: Descrição
- T002: Descrição
```

**6.2. Criar a Story**

Usar `jira_create_issue`:
- `project_key`: `project.key`
- `issue_type`: `hierarchy.story_type` (ex: "Story")
- `summary`: título da Phase (ex: "Phase 1: Autenticação de Usuário")
- `description`: descrição montada em 6.1
- `labels`: `defaults.story.labels`

Linkar ao Epic usando `jira_create_issue_link` com o relacionamento `hierarchy.relationships.epic_story`.

Salvar o key retornado (ex: "CMEI-101") como `story_key` para esta Phase.

**6.3. Executar sequência de transições da Story**

Para cada transição em `workflow.story_creation_transitions` (ex: ["Refiner", "Tec Refiner", "Ready To Dev"]):

1. Chamar `jira_get_transitions` para obter transições disponíveis da issue
2. Buscar a transição pelo nome (comparação case-insensitive)
3. Se encontrar → chamar `jira_transition_issue` com o ID da transição
4. Se não encontrar:
   - Se `workflow.fallback_to_sequence: true` → logar aviso e continuar para próxima
   - Se `fallback_to_sequence: false` → logar erro e parar a sequência desta Story

Exibir resultado ao final: `✅ CMEI-101 — Phase 1: <título> → Ready To Dev`

### 7. Criar Sub-tasks (se task_type não for vazio/none)

Se `hierarchy.task_type` não for `""` ou `"none"`:

Para cada task em cada Phase:

Usar `jira_create_issue`:
- `project_key`: `project.key`
- `issue_type`: `hierarchy.task_type` (ex: "Sub-task")
- `summary`: `<task_id>: <descrição>` (ex: "T001: Implementar endpoint de login")
- `labels`: `defaults.task.labels`
- `additional_fields`: `{"parent": "<story_key>"}` para linkar à Story

Salvar o key retornado no mapping.

Exibir: `  ✅ CMEI-102 — T001: <descrição>`

### 8. Salvar jira-mapping.json

Salvar mapping completo em `specs/<spec-name>/jira-mapping.json`:

```json
{
  "spec": "<spec-name>",
  "created_at": "<ISO 8601 timestamp>",
  "epic": {
    "key": "CMEI-100",
    "summary": "<título do epic>"
  },
  "stories": {
    "Phase 1": {
      "key": "CMEI-101",
      "summary": "<título da story>",
      "final_status": "Ready To Dev"
    }
  },
  "tasks": {
    "T001": {
      "key": "CMEI-102",
      "summary": "T001: <descrição>",
      "phase": "Phase 1"
    },
    "T002": {
      "key": "CMEI-103",
      "summary": "T002: <descrição>",
      "phase": "Phase 1"
    }
  }
}
```

### 9. Exibir resumo final

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Porto Jira — Hierarquia criada com sucesso
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Epic:    CMEI-100 — <título>
Stories: 3 criadas → Ready To Dev
Tasks:   12 sub-tasks criadas

CMEI-101 — Phase 1: <título> → Ready To Dev
  CMEI-102  T001: <descrição>
  CMEI-103  T002: <descrição>

CMEI-104 — Phase 2: <título> → Ready To Dev
  CMEI-105  T003: <descrição>
  ...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
