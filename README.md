# Spec-Kit Porto — Extensão SpecKit para Porto

Integração Jira customizada para os projetos da Porto, com stories ricas, workflow
próprio e sync granular de tasks.

## Instalação

```bash
specify extension add porto <github-tag-version-zip-url>
```

- `porto` é o nome da extensão.
- `<github-tag-version-zip-url>` é a URL do zip de uma tag/release deste
  repositório, no formato `https://github.com/<org>/spec-kit-porto/archive/refs/tags/<versão>.zip`
  (ex: `https://github.com/ciandt-pauloss/spec-kit-porto/archive/refs/tags/v1.0.0.zip`).

Para desenvolvimento local, use `--dev` apontando para o diretório do repositório —
isso cria um symlink e alterações nos arquivos da extensão são refletidas
imediatamente, sem precisar gerar uma nova tag:

```bash
specify extension add --dev /caminho/para/spec-kit-porto
```

## Por que essa extensão existe

O fluxo de trabalho da Porto no Jira tem particularidades que uma integração genérica
não cobre: workflow com 14 status (do Backlog ao Pronto, passando por refinamento
técnico, homologação e implantação), necessidade de mapear dependências externas
antes do planejamento técnico e stories que precisam nascer com contexto completo
(critérios de aceite INVEST, regras de negócio, Definition of Done) para reduzir
idas e vindas no refinamento. Esta extensão automatiza esse fluxo ponta a ponta,
sincronizando o progresso do `tasks.md` com o board real durante o `implement`.

## O que resolve

| # | Problema | Comportamento anterior | Comportamento desta extensão |
|---|----------|----------------------|------------------------------|
| 1 | Stories com descrição vaga | "Phase from spec: X\nTasks: T001..." | Contexto completo + critérios de aceite INVEST do spec.md |
| 2 | Sync somente no final | Sync manual após todo o implement | Hook `after_implement` + comando `sync-task` para sync individual |
| 3 | Stories criadas em Backlog | Sem transição após criação | Cascata automática: Backlog → Refiner → Tec Refiner → Ready To Dev |
| 4 | Status final vai para Done | Transição direta para Done | Navega pelo workflow até "Deploy" sem pular etapas |

## Estrutura

```
spec-kit-porto/
├── extension.yml                  # Manifesto da extensão
├── porto-config.template.yml      # Template de configuração
├── README.md
├── commands/
│   ├── dependencies.md            # Matriz de dependências externas (pré-plan)
│   ├── epic.md                    # Cria/atualiza o Epic no Jira (pré-plan)
│   ├── poc.md                     # POC de frontend para validar o fluxo (pré-plan)
│   ├── specstoissues.md           # Cria hierarquia Epic → Stories → Sub-tasks
│   ├── sync-status.md             # Sync batch de todas as tasks
│   └── sync-task.md               # Sync de uma task específica por ID
├── templates/
│   ├── dependencies-template.md   # Template do artefato dependencies.md
│   └── epic-template.md           # Template de descrição do Epic no Jira
└── scripts/
    └── python/
        └── generate_dependencies_xlsx.py  # Gera dependencies.xlsx (sem dependências externas)
```

## Configuração

Após instalar, copie o template e ajuste:

```bash
cp .specify/extensions/porto/porto-config.template.yml \
   .specify/extensions/porto/porto-config.yml
```

Edite `porto-config.yml` com as chaves do seu projeto e workflow.

## Fluxo completo (end-to-end)

Os comandos desta extensão se encaixam no ciclo de vida padrão do Spec Kit
(`specify` → `clarify` → `plan` → `tasks` → `implement`). A tabela abaixo mostra a
ordem em que tudo roda, do primeiro rascunho da spec até o sync final de status:

| Ordem | Etapa do Spec Kit | Comando desta extensão | Hook | Resultado |
|---|---|---|---|---|
| 1 | `speckit.specify` | — | — | `spec.md` criado |
| 2 | — | `speckit.porto.dependencies` | `after_specify` | `dependencies.md` + `dependencies.xlsx` |
| 3 | `speckit.clarify` | — | — | `spec.md` sem ambiguidades |
| 4 | — | `speckit.porto.epic` | `after_clarify` | Epic criado/atualizado no Jira |
| 5 | `speckit.plan` (antes) | `speckit.porto.poc` | `before_plan` | protótipo navegável em `poc/` |
| 6 | `speckit.plan` | — | — | `plan.md`, `research.md` |
| 7 | `speckit.tasks` | — | — | `tasks.md` |
| 8 | — | `speckit.porto.specstoissues` | `after_tasks` | Stories + Sub-tasks no Jira, `jira-mapping.json` |
| 9 | `speckit.implement` | `speckit.porto.sync-task` | manual, por task | sync individual conforme cada task avança |
| 10 | — | `speckit.porto.sync-status` | `after_implement` | sync em lote de todas as tasks pendentes |

Os passos 2, 4, 5 e 8 rodam via hook (todos `optional: true`, com confirmação do
usuário); o passo 9 é o único pensado para execução manual e repetida durante o
`implement`, dando visibilidade contínua sem esperar o fim da sessão.

## Comandos

Os três comandos abaixo rodam **antes do `/speckit.plan`** — foram pensados para o
fluxo de trabalho da Porto, onde spec.md precisa passar por mapeamento de
dependências, materialização do Epic e validação de UX antes do planejamento
técnico começar.

### `speckit.porto.dependencies`

Analisa `spec.md` (e `plan.md`/`research.md`, se já existirem) e monta a matriz de
dependências externas ao time responsável pela feature: outros times/verticais da
Porto, APIs, infraestrutura de terceiros e componentes compartilhados.

- Classifica cada dependência por Tipo (API, Infraestrutura, Componente, Serviço
  Externo), Vertical/Departamento, Responsável, Nome e Descrição
- Marca como `NEEDS CLARIFICATION` o que não puder ser determinado com confiança —
  nunca inventa responsável ou vertical
- Gera `specs/<spec-name>/dependencies.md` a partir de `templates/dependencies-template.md`
- Gera `specs/<spec-name>/dependencies.xlsx` com o mesmo conteúdo (via
  `scripts/python/generate_dependencies_xlsx.py`, sem dependências externas como
  openpyxl)

```bash
speckit run speckit.porto.dependencies
speckit run speckit.porto.dependencies --spec meu-spec
```

---

### `speckit.porto.epic`

Cria ou atualiza o Epic no Jira a partir do `spec.md`, usando um template de boas
práticas de escrita de épicos (`templates/epic-template.md`). Diferente do
`specstoissues`, não cria Stories/Sub-tasks — apenas o Epic, permitindo validá-lo
com stakeholders antes do plan e das tasks existirem.

```bash
speckit run speckit.porto.epic                        # cria novo Epic
speckit run speckit.porto.epic --project CMEI          # cria em um projeto específico
speckit run speckit.porto.epic --epic CMEI-100         # atualiza um Epic existente
```

Se o Epic já tiver sido criado por este comando, `speckit.porto.specstoissues`
reaproveita o key salvo em `jira-mapping.json` em vez de criar um novo.

---

### `speckit.porto.poc`

Gera um protótipo de frontend a partir do `spec.md`, usando a mesma stack já
adotada pelo projeto (detectada via `plan.md`, `constitution.md` ou arquivos de
configuração do repositório). Cobre por padrão apenas as User Stories P1, usa
dados mockados e não é código de produção — o objetivo é validar o fluxo/UX antes
de investir no planejamento técnico completo.

```bash
speckit run speckit.porto.poc
speckit run speckit.porto.poc --out poc/meu-fluxo
```

---

### `speckit.porto.specstoissues`

Cria a hierarquia Epic → Stories → Sub-tasks no Jira a partir do `spec.md` e `tasks.md`.

- Extrai critérios de aceite INVEST de cada User Story do spec.md
- Cria Stories com descrição rica (narrativa + ACs + regras + DoD + tasks)
- Após criar cada Story, executa a cascata de transições configurada
- Salva `jira-mapping.json` para uso pelos comandos de sync

```bash
speckit run speckit.porto.specstoissues
speckit run speckit.porto.specstoissues --spec meu-spec
```

**Alias:** `speckit.specstoissues`

---

### `speckit.porto.sync-status`

Lê o `tasks.md`, compara com `jira-mapping.json` e transiciona todas as issues
desatualizadas para o status correto no workflow.

- `[x]` → navega até `workflow.task_complete_status` (ex: "Deploy")
- `[~]` → transiciona para `workflow.task_in_progress_status` (ex: "In Progress")
- `[ ]` → sem transição

```bash
speckit run speckit.porto.sync-status
```

**Alias:** `speckit.jira.sync-status`

---

### `speckit.porto.sync-task`

Sincroniza uma task específica por ID. Use durante o implement para visibilidade
contínua sem esperar o final da sessão.

```bash
speckit run speckit.porto.sync-task T001
speckit run speckit.porto.sync-task --task T001 --status in_progress
speckit run speckit.porto.sync-task --task T002 --status done
```

## Hooks automáticos

A extensão registra cinco hooks no manifesto — todos `optional: true` (o usuário
confirma antes da execução):

| Hook | Comando | Prompt |
|------|---------|--------|
| `after_specify` | `dependencies` | "Gerar matriz de dependências...?" |
| `after_clarify` | `epic` | "Criar/atualizar o Epic no Jira...?" |
| `before_plan` | `poc` | "Gerar POC de frontend...?" |
| `after_tasks` | `specstoissues` | "Criar issues no Jira com detalhes completos...?" |
| `after_implement` | `sync-status` | "Sincronizar tasks implementadas para o Jira?" |

**Nota**: cada extensão só pode registrar um hook por evento do ciclo de vida —
por isso os três comandos pré-plan foram distribuídos em eventos diferentes
(`after_specify`, `after_clarify`, `before_plan`), todos entre o `specify` e o
`plan`. Quem quiser rodar mais de um manualmente pode chamar os comandos
diretamente.

## Configuração do extensions.yml

Após instalar a extensão, os hooks `after_specify`, `after_clarify` e `before_plan`
são registrados automaticamente pelo manifesto. Falta apenas adicionar o hook
`after_implement` no `extensions.yml` do repositório:

```yaml
after_implement:
  - extension: git
    command: speckit.git.commit
    enabled: true
    optional: true
    prompt: "Commit das implementações?"
  - extension: porto
    command: speckit.porto.sync-status
    enabled: true
    optional: true
    prompt: "Sincronizar tasks implementadas para o Jira?"
```

O hook `after_tasks` também é registrado automaticamente pelo manifesto da extensão.

## Workflow configurado

O workflow padrão da porto:

```
Backlog → Em Refinamento → Em Refinamento Técnico → Preparado Para Desenvolviento → Selecionado para Desenvolvimento → Em Desenvolvimento → Pronto para Teste → Em Testes → Testado → Em Homologação → Homologado → Preparação para Implantação → Pronto para Implantar → Pronto
```

- **Stories criadas** percorrem: Backlog → Em Refinamento → Selecionado para Desenvolvimento
- **Tasks completadas** (`[x]`) vão para: Pronto
- **Tasks em andamento** (`[~]`) vão para: Fazendo

O campo `fallback_to_sequence: true` garante navegação passo a passo quando
não há transição direta disponível entre dois estados.
