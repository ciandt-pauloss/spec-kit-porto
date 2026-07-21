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
- `--task T001` (ou apenas `T001`) — ID da task a sincronizar (obrigatório)
- `--status done|in_progress` — status alvo (padrão: `done` → usa `workflow.task_complete_status`)
- `--spec <nome>` — spec opcional (auto-detectado se não informado)

## Steps

### 1. Carregar configuração e detectar spec

Detectar spec na mesma ordem dos outros comandos:
1. Argumento `--spec <nome>`
2. Branch git atual
3. Diretório atual
4. Único spec disponível

Carregar `.specify/extensions/porto/porto-config.yml`.

Extrair:
- `mcp_server`
- `workflow.fallback_to_sequence`
- `status_mapping.story.*` e `status_mapping.task.*`

### 2. Parsear argumentos

Extrair de `$ARGUMENTS`:
- **task_id**: valor de `--task` ou primeiro argumento posicional (ex: `T001`, `t001` → normalizar para maiúsculas)
- **status_arg**: valor de `--status` (`done` ou `in_progress`; padrão: `done`)
- **spec**: valor de `--spec` (se informado)

Se `task_id` não for informado, exibir uso e encerrar:
```
Uso: speckit.porto.sync-task --task T001 [--status done|in_progress] [--spec nome]
```

Determinar o bloco do `status_mapping` a usar consultando o tipo da issue no `jira-mapping.json`:
- Tipo Story → `status_mapping.story`
- Tipo Sub-task ou Task → `status_mapping.task`

Determinar status alvo dentro do bloco:
- `--status done` ou padrão → bloco `.completed` (ex: "Deploy")
- `--status in_progress` → bloco `.in_progress` (ex: "In Progress")

### 3. Encontrar o Jira key no jira-mapping.json

Ler `specs/<spec-name>/jira-mapping.json`.

Se não existir, exibir erro:
```
❌ jira-mapping.json não encontrado em specs/<spec-name>/
   Execute primeiro: speckit.porto.specstoissues
```

Buscar `task_id` em `mapping.tasks` (comparação case-insensitive: T001 == t001).

Se não encontrar, exibir erro com tasks disponíveis:
```
❌ Task T001 não encontrada no jira-mapping.json
   Tasks disponíveis: T001, T002, T003, ...
```

Extrair o Jira key (ex: "CMEI-102") e o summary da task.

### 4. Obter status atual da issue

Chamar `jira_get_issue` com o Jira key para obter o status atual.

Se o status atual já for igual ao status alvo:
```
⏭️  T001 (CMEI-102) já está em <status> — nenhuma ação necessária
```
Encerrar com sucesso.

### 5. Transicionar a issue para o status alvo

Chamar `jira_get_transitions` para listar transições disponíveis.

**Tentativa 1 — Transição direta:**
Buscar transição com `to.name` igual ao status alvo (case-insensitive).
Se encontrar → executar `jira_transition_issue`.

**Tentativa 2 — Navegação sequencial (se `fallback_to_sequence: true`):**
Quando não há transição direta:
1. Executar a próxima transição disponível em direção ao alvo
2. Verificar novo status após cada transição
3. Repetir até chegar no alvo (máximo 10 iterações)
4. Se travar, exibir erro com estado atual e encerrar

### 6. Adicionar comentário na issue

Após transicionar com sucesso:
```
Status atualizado via spec-kit porto
Task: T001 | Spec: <spec-name> | Comando: sync-task
```

### 7. Exibir resultado

**Sucesso:**
```
✅ T001 (CMEI-102) → Deploy
🔗 https://<dominio>.atlassian.net/browse/CMEI-102
```

**Erro:**
```
❌ T001 (CMEI-102) — falha ao transicionar para Deploy
   Status atual: In Progress
   Transições disponíveis: Deploy, Blocked
   Motivo: <descrição do erro>
```
