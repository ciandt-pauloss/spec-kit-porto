Spec: Extensão SpecKit porto
Objetivo
Criar uma extensão SpecKit customizada (porto) como projeto standalone numa pasta separada, depois instalá-la em modo dev no repositório central-specs. Ela substitui completamente a extensão comunitária spec-kit-jira — após instalar a porto, a extensão jira pode ser desinstalada.

Problemas que a extensão resolve
#	Problema	Comportamento atual	Comportamento desejado
1	Stories com descrição vaga	"Phase from spec: X\n\nTasks: T001, T002..."	Contexto completo + critérios de aceite INVEST extraídos do spec.md
2	Sync de tasks somente no final	Sync manual/batch após todo o implement	Hook automático after_implement + comando sync-task para sync individual
3	Stories criadas em Backlog	Nenhuma transição de status após criação	Cascata automática: Backlog → Refiner → Tec Refiner → Ready To Dev
4	Status final vai para Done diretamente	Transição direta para "Done"	Navega pelo workflow até "Deploy" (status de revisão) sem pular etapas
Estrutura do Projeto Standalone
Criar a extensão em uma pasta separada (ex: /Projects/porto/porto-extension/):

porto-extension/
├── extension.yml                  # Manifesto da extensão
├── porto-config.template.yml      # Template copiado no install
├── README.md
└── commands/
    ├── specstoissues.md           # Cria hierarquia Jira com ACs + transição stories
    ├── sync-status.md             # Sync batch com workflow customizado
    └── sync-task.md               # Sync de uma task específica por ID
Arquivo: extension.yml
schema_version: "1.0"

extension:
  id: "porto"
  name: "Porto Jira Integration"
  version: "1.0.0"
  description: "Integração Jira customizada para porto: stories ricas, workflow próprio e sync granular"
  author: "Paulo Henrique"
  license: "MIT"

requires:
  speckit_version: ">=0.1.0"

provides:
  commands:
    - name: "speckit.porto.specstoissues"
      file: "commands/specstoissues.md"
      description: "Cria hierarquia Jira com ACs do spec.md e transiciona stories para Ready To Dev"
      aliases: ["speckit.specstoissues"]

    - name: "speckit.porto.sync-status"
      file: "commands/sync-status.md"
      description: "Sincroniza status de todas as tasks para o workflow do Jira"
      aliases: ["speckit.jira.sync-status"]

    - name: "speckit.porto.sync-task"
      file: "commands/sync-task.md"
      description: "Sincroniza uma task específica por ID durante o implement"

  config:
    - name: "porto-config.yml"
      template: "porto-config.template.yml"
      description: "Configuração da integração Jira com workflow customizado"
      required: true

hooks:
  after_tasks:
    command: "speckit.porto.specstoissues"
    optional: true
    prompt: "Criar issues no Jira com detalhes completos e transicionar stories para Ready To Dev?"
    description: "Cria hierarquia Jira após geração de tasks"

  after_implement:
    command: "speckit.porto.sync-status"
    optional: true
    prompt: "Sincronizar status das tasks implementadas para o Jira?"
    description: "Sync de status após sessão de implement"

tags:
  - "jira"
  - "atlassian"
  - "issue-tracking"
  - "porto"
Arquivo: porto-config.template.yml
# Configuração da integração Jira — copie para porto-config.yml e ajuste

# Servidor MCP (deve expor ferramentas de transição: transition_list, issue_transition)
mcp_server: "mcp-atlassian"

# Projeto Jira
project:
  key: "CMEI"

# Hierarquia de issues
hierarchy:
  epic_type: "Epic"
  story_type: "Story"
  task_type: "Sub-task"   # "" ou "none" para modo 2-level (Epic → Stories apenas)
  relationships:
    epic_story: "Epic Link"
    story_task: "Parent"
    epic_task: "Epic Link"

# Labels padrão por nível
defaults:
  epic:
    labels: ["SDD"]
    custom_fields: {}
  story:
    labels: ["SDD"]
    custom_fields: {}
  task:
    labels: []
    custom_fields: {}

# Mapeamento de campos customizados (descobertos via /speckit.jira.discover-fields)
field_mappings: {}

# Workflow customizado — coração desta extensão
workflow:
  # Sequência de transições executada após criar cada Story
  # O comando irá chamar transition_list e executar cada transição em ordem
  story_creation_transitions:
    - "Refiner"
    - "Tec Refiner"
    - "Ready To Dev"

  # Status alvo ao marcar task como [x] — evita ir para Done diretamente
  # O comando navega pelo workflow até chegar neste status
  task_complete_status: "Deploy"

  # Status ao marcar task como [~] (in progress)
  task_in_progress_status: "In Progress"

  # Se a transição direta não existir, navegar pela sequência disponível
  fallback_to_sequence: true

# Mapeamento de checkboxes do tasks.md
status_mapping:
  completed: "Deploy"       # [x] no tasks.md
  in_progress: "In Progress" # [~] no tasks.md
  pending: "Ready To Dev"   # [ ] no tasks.md
Arquivo: commands/specstoissues.md
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

1. MCP server configurado e rodando
2. `.specify/extensions/porto/porto-config.yml` existe e está configurado
3. `specs/<spec-name>/spec.md` e `specs/<spec-name>/tasks.md` existem

## User Input

$ARGUMENTS

Aceita argumento opcional `--spec <nome>` para especificar qual spec usar.

## Steps

### 1. Detectar spec e carregar configuração

Detectar spec na mesma ordem da extensão jira padrão:
1. Argumento `--spec <nome>`
2. Nome do branch git atual
3. Diretório atual
4. Único spec disponível

Carregar `.specify/extensions/porto/porto-config.yml`.

### 2. Parse do spec.md extraindo User Stories completas

Ler o `spec.md` e extrair cada User Story com todo seu conteúdo, incluindo:
- Título da User Story
- Contexto / Como... Quero... Para...
- Critérios de aceite
- Regras de negócio
- Definição de pronto

Montar um mapa: `{ "US-01": { titulo, contexto, criterios, regras, dod }, ... }`

Para a correspondência com as Phases do tasks.md, usar:
- Número da US (US-01 → Phase 1)
- Palavras-chave comuns no título
- Ordem de aparecimento (Phase N → N-ésima User Story)

### 3. Parse do tasks.md extraindo fases e tasks

Igual à extensão jira padrão: extrair Phases (## Phase N: ...) e tasks por fase.

### 4. Verificar mapping existente

Checar se `specs/<spec-name>/jira-mapping.json` existe. Se sim, perguntar ao usuário:
- Pular issues já existentes e criar apenas as faltantes
- Recriar tudo (gera duplicatas)
- Abortar

### 5. Criar Epic a partir do spec.md

Criar o Epic com o conteúdo completo do spec.md como descrição.

### 6. Para cada Phase: criar Story com descrição rica

**Montar a descrição da Story** combinando:
- User Story correspondente extraída do spec.md (passo 2)
- Lista de tasks da fase

Formato da descrição:
Contexto
{contexto da user story do spec.md}

Como uma história de usuário
Como {role}, quero {ação}, para {objetivo}

Critérios de Aceite
{critérios de aceite do spec.md em formato INVEST}

Regras de Negócio
{regras extraídas do spec.md, se houver}

Definição de Pronto
{DoD do spec.md, se houver}

Tasks de Implementação
T001: {descrição}
T002: {descrição}

Criar a Story com essa descrição e linkar ao Epic.

**Após criar cada Story, executar a sequência de transições:**
workflow.story_creation_transitions = ["Refiner", "Tec Refiner", "Ready To Dev"]


Para cada transição na sequência:
1. Chamar `jira_get_transitions` para obter transições disponíveis
2. Buscar a transição pelo nome (case-insensitive)
3. Se encontrar, chamar `jira_transition_issue`
4. Se não encontrar e `fallback_to_sequence: true`, continuar para próxima

Exibir resultado: `✅ CMEI-101 - Phase 1: ... → Ready To Dev`

### 7. Criar Sub-tasks (se task_type não for vazio)

Igual à extensão jira padrão: criar uma issue por task e linkar à Story.

### 8. Salvar jira-mapping.json

Salvar mapping completo em `specs/<spec-name>/jira-mapping.json`.

### 9. Exibir resumo

Exibir resumo com Epic, Stories, Sub-tasks criadas e status final de cada Story.
Arquivo: commands/sync-status.md
---
description: "Sincroniza status de tasks completadas/em andamento para o Jira respeitando o workflow configurado"
tools:
  - '{mcp_server}/jira_update_issue'
  - '{mcp_server}/jira_get_issue'
  - '{mcp_server}/jira_get_transitions'
  - '{mcp_server}/jira_transition_issue'
  - '{mcp_server}/jira_add_comment'
---

# Sincronizar Status das Tasks para o Jira

Lê o tasks.md, compara com jira-mapping.json e transiciona as issues Jira
para o status correto. Navega pelo workflow em vez de tentar transição direta,
respeitando as etapas obrigatórias do workflow do projeto.

## User Input

$ARGUMENTS

## Steps

### 1. Carregar configuração e detectar spec

Carregar `.specify/extensions/porto/porto-config.yml` e detectar spec.

### 2. Ler tasks.md e jira-mapping.json

Identificar o status local de cada task:
- `[x]` → completed (alvo: `workflow.task_complete_status`, ex: "Deploy")
- `[~]` → in_progress (alvo: `workflow.task_in_progress_status`, ex: "In Progress")
- `[ ]` → pending (sem transição)

### 3. Para cada task que precisa ser atualizada

1. Obter o Jira key do jira-mapping.json
2. Buscar o status atual da issue (`jira_get_issue`)
3. Se o status atual já for o alvo, pular (idempotente)
4. Obter transições disponíveis (`jira_get_transitions`)
5. Tentar encontrar a transição direta para o status alvo
6. Se não existir transição direta e `fallback_to_sequence: true`:
   - Navegar pelas transições disponíveis em ordem até chegar no status alvo
   - Parar se chegar num estado sem saída para o alvo
7. Adicionar comentário na issue: "Status atualizado via spec-kit porto"
8. Exibir: `✅ CMEI-45 (T001) → Deploy`

### 4. Atualizar Epic com percentual de progresso

Calcular % de tasks completadas e atualizar descrição do Epic.

### 5. Salvar log e exibir resumo
Arquivo: commands/sync-task.md
---
description: "Sincroniza uma task específica por ID para o Jira — use durante o implement para atualizações granulares"
tools:
  - '{mcp_server}/jira_get_issue'
  - '{mcp_server}/jira_get_transitions'
  - '{mcp_server}/jira_transition_issue'
  - '{mcp_server}/jira_add_comment'
---

# Sincronizar Task Específica para o Jira

Sincroniza uma única task por ID (ex: T001) durante o implement.
Use este comando após completar cada task individualmente para dar visibilidade
contínua no Jira sem esperar o final do implement.

## User Input

$ARGUMENTS

Aceita:
- `--task T001` (ou apenas `T001`) — ID da task a sincronizar
- `--status done|in_progress` — status alvo (padrão: done → usa workflow.task_complete_status)
- `--spec <nome>` — spec opcional (auto-detectado se não informado)

## Steps

### 1. Carregar configuração e detectar spec

### 2. Encontrar o Jira key no jira-mapping.json

Buscar pelo task ID (ex: T001) no jira-mapping.json.
Se não encontrar, exibir erro claro.

### 3. Transicionar a issue

Igual ao sync-status.md mas apenas para esta issue.

Status alvo:
- `--status done` → `workflow.task_complete_status` (ex: "Deploy")
- `--status in_progress` → `workflow.task_in_progress_status` (ex: "In Progress")

### 4. Exibir resultado

`✅ T001 (CMEI-45) → Deploy`
`🔗 https://cmei.atlassian.net/browse/CMEI-45`
Instalação
Após criar todos os arquivos na pasta separada:

# Instalar em modo dev no central-specs
cd /caminho/para/central-specs
specify extension add --dev /caminho/para/porto-extension

# Desinstalar a extensão jira comunitária (não será mais necessária)
specify extension remove jira
O specify extension add --dev cria um symlink — qualquer mudança nos arquivos da extensão é refletida imediatamente sem precisar reinstalar.

Mudança necessária no extensions.yml após instalação
Com a extensão jira desinstalada, os hooks antigos dela serão removidos automaticamente do registry. O extensions.yml precisará apenas adicionar o hook after_implement da nova extensão:

after_implement:
  - extension: git
    command: speckit.git.commit
    enabled: true
    optional: true
    prompt: "Commit das implementações?"
  - extension: porto                # ← novo
    command: speckit.porto.sync-status
    enabled: true
    optional: true
    prompt: "Sincronizar tasks implementadas para o Jira?"
O hook after_tasks será registrado automaticamente pelo manifesto da extensão.