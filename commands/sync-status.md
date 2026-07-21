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

Aceita argumento opcional `--spec <nome>` para especificar qual spec usar.

## Steps

### 1. Carregar configuração e detectar spec

Detectar spec na mesma ordem do specstoissues:
1. Argumento `--spec <nome>`
2. Branch git atual
3. Diretório atual
4. Único spec disponível

Carregar `.specify/extensions/porto/porto-config.yml`.

Extrair:
- `mcp_server`
- `workflow.fallback_to_sequence`
- `status_mapping.story.*` (alvos para Stories)
- `status_mapping.task.*` (alvos para Sub-tasks e Tasks)

### 2. Ler tasks.md e jira-mapping.json

Ler `specs/<spec-name>/tasks.md` e classificar cada task:
- `[x]` → **completed** → status alvo via `status_mapping` (veja abaixo)
- `[~]` → **in_progress** → status alvo via `status_mapping`
- `[ ]` → **pending** → sem transição necessária

Para determinar qual bloco do `status_mapping` usar, consultar o tipo da issue
no `jira-mapping.json`:
- Tipo Story → usar `status_mapping.story`
- Tipo Sub-task ou Task → usar `status_mapping.task`

Ler `specs/<spec-name>/jira-mapping.json` para obter o Jira key de cada task.

Se o jira-mapping.json não existir, exibir erro:
```
❌ jira-mapping.json não encontrado em specs/<spec-name>/
   Execute primeiro: speckit.porto.specstoissues
```

### 3. Para cada task que precisa ser atualizada

Processar apenas tasks com status `[x]` ou `[~]` (ignorar `[ ]`).

Para cada task a atualizar:

**3.1. Obter Jira key**

Buscar o task ID (ex: "T001") no `jira-mapping.json → tasks`.
Se não encontrar, logar aviso e continuar para próxima task.

**3.2. Obter status atual da issue**

Chamar `jira_get_issue` com o Jira key.
Extrair o status atual (ex: "Ready To Dev").

**3.3. Verificar idempotência**

Se o status atual já for igual ao status alvo → pular com log:
`⏭️  CMEI-102 (T001) já está em <status> — pulando`

**3.4. Navegar pelo workflow até o status alvo**

Chamar `jira_get_transitions` para obter transições disponíveis.

**Tentativa 1 — Transição direta:**
Buscar transição cujo `to.name` (case-insensitive) seja igual ao status alvo.
Se encontrar → executar e ir para 3.5.

**Tentativa 2 — Navegação sequencial (se `fallback_to_sequence: true`):**
Quando não há transição direta para o alvo, navegar passo a passo:
1. Obter transições disponíveis no estado atual
2. Executar a primeira transição disponível que aproxima do alvo (evitar voltar atrás)
3. Repetir até chegar no status alvo ou até não haver mais transições
4. Se travar em loop (estado sem saída para o alvo), logar erro e abortar esta task

Limite máximo de 10 iterações por task para evitar loop infinito.

**3.5. Adicionar comentário na issue**

Após transicionar com sucesso:
```
Status atualizado via spec-kit porto
Task: T001 | Spec: <spec-name>
```

**3.6. Exibir resultado**

Sucesso: `✅ CMEI-102 (T001) → Deploy`
Erro:    `❌ CMEI-102 (T001) — falha ao transicionar: <motivo>`

### 4. Atualizar Epic com percentual de progresso

Após processar todas as tasks:

1. Calcular estatísticas:
   - Total de tasks no tasks.md
   - Quantidade com `[x]` (completadas)
   - Quantidade com `[~]` (em andamento)
   - Percentual concluído: `(completadas / total) * 100`

2. Atualizar a descrição do Epic (`jira_update_issue`) adicionando ao início:

```markdown
## Progresso

**{percentual}% concluído** ({completadas}/{total} tasks)
Atualizado em: {data/hora}

---

{conteúdo original da descrição}
```

### 5. Salvar log e exibir resumo

Exibir resumo final:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Porto Jira — Sync de status concluído
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tasks processadas: 8
  ✅ Transicionadas com sucesso: 6
  ⏭️  Já no status correto:       1
  ❌ Falhas:                      1

CMEI-102 (T001) → Deploy
CMEI-103 (T002) → Deploy
CMEI-104 (T003) → In Progress
...

Epic atualizado: CMEI-100 — 75% concluído (6/8 tasks)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
