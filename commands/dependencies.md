---
description: "Analisa spec.md e demais assets da feature para montar a matriz de dependências externas (times/verticais, APIs, infraestrutura, componentes) e gera dependencies.md + dependencies.xlsx"
---

# Gerar Matriz de Dependências

Este comando roda **antes do `/speckit.plan`**. Ele lê o `spec.md` (e, se existirem,
`research.md`/`plan.md` de execuções anteriores) e identifica tudo que a feature
depende de fora do time responsável: outros times/verticais da Porto, APIs,
infraestrutura de terceiros e componentes compartilhados. O resultado é usado para
antecipar bloqueios e alinhamentos antes de o planejamento técnico começar.

## Pré-requisitos

1. `specs/<spec-name>/spec.md` existe
2. `.specify/extensions/porto/porto-config.yml` (opcional — usa defaults se ausente)
3. Python 3 disponível no PATH (usado apenas para gerar o `.xlsx`; sem dependências
   externas como openpyxl)

## User Input

$ARGUMENTS

Aceita argumento opcional `--spec <nome>` para especificar qual spec usar.

## Steps

### 1. Detectar spec e carregar configuração

Detectar spec na mesma ordem dos demais comandos da extensão:
1. Argumento `--spec <nome>`
2. Branch git atual
3. Diretório atual
4. Único spec disponível

Carregar `.specify/extensions/porto/porto-config.yml` se existir. Extrair:
- `dependencies.known_verticals` (lista de verticais/departamentos conhecidos, usada
  como sugestão de padronização — pode não existir)
- `dependencies.generate_xlsx` (padrão: `true` se ausente)

### 2. Ler os artefatos da feature

Ler `specs/<spec-name>/spec.md` por completo. Se existirem, ler também
`specs/<spec-name>/plan.md` e `specs/<spec-name>/research.md` — eles podem conter
detalhes técnicos sobre integrações que o spec.md não menciona explicitamente.

### 3. Identificar dependências externas

Procurar, em todo o conteúdo lido, menções que indiquem dependência de algo externo
ao time responsável pela feature:

- **APIs/serviços**: "integra com", "consome o serviço", "API de", "chama o endpoint"
- **Times/verticais**: "time de", "squad", "necessita alinhamento com", "depende da
  aprovação de", menções a áreas/departamentos da Porto
- **Infraestrutura**: filas, gateways, provedores cloud, serviços de terceiros,
  bancos de dados compartilhados fora do domínio da feature
- **Componentes**: design system compartilhado, bibliotecas internas de outros times

Para cada dependência identificada, extrair:
- **Tipo**: `API` | `Infraestrutura` | `Componente` | `Serviço Externo`
- **Vertical / Departamento**: a área da Porto responsável (ou "Terceiro" para
  fornecedores externos à empresa)
- **Responsável**: pessoa ou time citado no texto, se houver
- **Nome**: nome da API/componente/recurso
- **Descrição**: o que é consumido/necessário e por quê

**Não inventar informação.** Quando Responsável, Vertical ou Nome não puderem ser
determinados com confiança a partir do texto, marcar o campo como
`NEEDS CLARIFICATION: <o que falta>` em vez de supor um valor.

### 4. Padronizar verticais conhecidas

Se `dependencies.known_verticals` estiver configurado, tentar casar cada vertical
identificada com um item da lista (comparação case-insensitive, tolerante a
variações). Se não houver correspondência razoável, manter o nome extraído do texto
e avisar ao final que é um valor novo, não presente na lista configurada.

### 5. Renderizar dependencies.md

Usar `templates/dependencies-template.md` como base e preencher:
- Cabeçalho (nome da feature, data, spec de origem)
- Tabela de dependências identificadas (passo 3)
- Seção "Itens Pendentes de Esclarecimento" com todo item marcado
  `NEEDS CLARIFICATION`

Salvar em `specs/<spec-name>/dependencies.md`.

### 6. Gerar dependencies.xlsx

Se `dependencies.generate_xlsx` for `true` (padrão):

1. Montar um JSON temporário no formato:
   ```json
   {
     "sheet_name": "Dependencies",
     "headers": ["Tipo", "Vertical / Departamento", "Responsável", "Nome", "Descrição"],
     "rows": [["API", "...", "...", "...", "..."]]
   }
   ```
2. Executar:
   ```bash
   python3 .specify/extensions/porto/scripts/python/generate_dependencies_xlsx.py <json-tmp> specs/<spec-name>/dependencies.xlsx
   ```
3. Remover o JSON temporário após a geração.

**Graceful degradation**: se `python3` não estiver disponível no PATH ou o script
falhar, avisar o usuário e manter apenas o `dependencies.md` — não abortar o
comando por causa da planilha.

### 7. Exibir resumo

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Porto — Matriz de Dependências gerada
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Dependências identificadas: 5
  API: 2 | Infraestrutura: 1 | Componente: 1 | Serviço Externo: 1
Pendentes de esclarecimento: 1

📄 specs/<spec-name>/dependencies.md
📊 specs/<spec-name>/dependencies.xlsx
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
