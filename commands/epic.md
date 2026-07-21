---
description: "Cria ou atualiza o Epic no Jira a partir do spec.md, aplicando boas práticas de escrita de épicos"
tools:
  - '{mcp_server}/jira_create_issue'
  - '{mcp_server}/jira_update_issue'
  - '{mcp_server}/jira_get_issue'
  - '{mcp_server}/jira_search'
---

# Criar ou Atualizar Epic no Jira

Este comando roda **antes do `/speckit.plan`**. Ele materializa (ou atualiza) o Epic
no Jira a partir do `spec.md`, usando um template de boas práticas de escrita de
épicos — diferente do `speckit.porto.specstoissues`, que cria a hierarquia completa
(Epic → Stories → Sub-tasks) apenas depois que `tasks.md` existe.

## Pré-requisitos

1. MCP server `mcp-atlassian` configurado e rodando
2. `.specify/extensions/porto/porto-config.yml` existe e está configurado
3. `specs/<spec-name>/spec.md` existe

## User Input

$ARGUMENTS

Aceita:
- `--epic <KEY>` — atualiza um epic já existente (ex: `--epic CMEI-100`)
- `--project <KEY>` — cria em um projeto Jira específico (padrão: `project.key` da
  config, usado quando `--epic` não é informado)
- `--spec <nome>` — spec opcional (auto-detectado se não informado)

## Steps

### 1. Detectar spec e carregar configuração

Detectar spec na mesma ordem dos demais comandos da extensão. Carregar
`.specify/extensions/porto/porto-config.yml`. Extrair:
- `mcp_server`
- `project.key`
- `hierarchy.epic_type` (ex: "Epic")
- `epic.labels` e `epic.custom_fields` (seção `epic:` da config; se ausente, usar
  `defaults.epic.labels`/`defaults.epic.custom_fields` como fallback)

### 2. Parsear argumentos

Extrair `--epic`, `--project` e `--spec` de `$ARGUMENTS`. Se ambos `--epic` e
`--project` forem informados, priorizar `--epic` (atualização) e avisar que
`--project` foi ignorado.

### 3. Ler spec.md e montar o conteúdo do épico

Ler `specs/<spec-name>/spec.md` completo e extrair:
- Título (H1)
- Problema/objetivo de negócio (visão geral da feature)
- Contexto (motivação, por trás da priorização)
- Escopo: itens cobertos pelas User Stories vs. Edge Cases/exclusões explícitas
- Success Criteria (`SC-00N`)
- Riscos ou premissas mencionadas, se houver

Se `specs/<spec-name>/dependencies.md` existir (gerado por
`speckit.porto.dependencies`), ler sua tabela de dependências e resumir as linhas
mais relevantes (Vertical + Nome + Descrição) para a seção "Dependências" do épico.

### 4. Renderizar a descrição do épico

Usar `templates/epic-template.md` como base e preencher cada seção com o conteúdo
extraído no passo 3. Omitir seções para as quais não há conteúdo disponível no
spec.md (não deixar o placeholder do template no resultado final).

### 5. Criar ou atualizar o Epic

**Se `--epic <KEY>` foi informado:**

1. `jira_get_issue` para validar que a issue existe e é do tipo `hierarchy.epic_type`
   - Se não for um Epic, exibir erro e encerrar sem alterar a issue
2. `jira_update_issue` atualizando `summary` (se o título mudou) e `description`
   com o conteúdo renderizado no passo 4
3. Exibir: `✅ Epic atualizado: <KEY> — <título>`

**Caso contrário (criar novo):**

1. `jira_create_issue`:
   - `project_key`: `--project` informado, ou `project.key` da config
   - `issue_type`: `hierarchy.epic_type`
   - `summary`: título do spec.md
   - `description`: conteúdo renderizado no passo 4
   - `labels`: `epic.labels`
   - Campos customizados de `epic.custom_fields`, se houver
2. Salvar o key retornado (ex: "CMEI-100") em `specs/<spec-name>/jira-mapping.json`,
   no campo `epic.key` — criando o arquivo se ainda não existir, ou atualizando o
   campo `epic` se o arquivo já existir (sem sobrescrever `stories`/`tasks`
   eventualmente já presentes)
3. Exibir: `✅ Epic criado: <KEY> — <título>`

### 6. Exibir link

```
🔗 https://<domínio>.atlassian.net/browse/<KEY>
```

## Nota sobre uso conjunto com specstoissues

Quando `speckit.porto.epic` roda antes de `speckit.porto.specstoissues`, o
`jira-mapping.json` já contém `epic.key`. O `specstoissues` deve checar esse campo
antes de criar um novo Epic — reaproveitando o épico existente em vez de duplicá-lo.
