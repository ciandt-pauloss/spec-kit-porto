---
description: "Gera um protótipo de frontend a partir do spec.md, usando a stack do projeto (constitution/plan), para validar o fluxo da história antes do planejamento técnico"
---

# Gerar POC de Frontend

Este comando roda **antes do `/speckit.plan`**. Ele materializa o que foi definido no
`spec.md` em um protótipo navegável de frontend, usando a mesma tecnologia já adotada
pelo projeto — o objetivo é validar o fluxo/UX da história com stakeholders antes de
investir no planejamento técnico completo. **Não é código de produção**: usa dados
mockados, não se conecta a serviços reais e não precisa de testes automatizados.

## Pré-requisitos

1. `specs/<spec-name>/spec.md` existe
2. Stack tecnológica identificável via `plan.md` da spec, `.specify/memory/constitution.md`
   ou arquivos de configuração do repositório (`package.json`, etc.)

## User Input

$ARGUMENTS

Aceita:
- `--spec <nome>` — spec opcional (auto-detectado se não informado)
- `--out <dir>` — diretório de saída (padrão: `poc.output_dir` da config, com
  `{spec_name}` substituído pelo nome da spec — ex: `poc/003-user-auth/`)

## Steps

### 1. Detectar spec e diretório de saída

Detectar spec na mesma ordem dos demais comandos da extensão. Carregar
`.specify/extensions/porto/porto-config.yml` se existir e extrair `poc.output_dir`
(padrão: `poc/{spec_name}` se ausente/config não existir). Resolver `{spec_name}` e
aplicar `--out`, se informado, como override.

### 2. Detectar a stack tecnológica do projeto

Nesta ordem de prioridade, até encontrar informação suficiente:

1. `specs/<spec-name>/plan.md` → seção "Technical Context" (`Language/Version`,
   `Primary Dependencies`, `Project Type`)
2. `.specify/memory/constitution.md` → menções a stack/frameworks obrigatórios
3. Arquivos de configuração na raiz do repositório (`package.json`, `pom.xml`,
   `requirements.txt`, etc.) e sua pasta de frontend, se houver uma separada

Se nenhuma fonte tiver informação suficiente para determinar a stack de frontend,
**perguntar ao usuário** qual tecnologia usar antes de prosseguir — não assumir uma
stack arbitrária.

### 3. Ler o spec.md e definir o escopo da POC

Ler `specs/<spec-name>/spec.md` e, para cada User Story (priorizando P1 — o MVP),
extrair:
- Telas/fluxos envolvidos
- Campos de formulário e validações mencionadas
- Estados relevantes (carregando, erro, vazio, sucesso)
- Ações do usuário e resultado esperado de cada uma

**Escopo da POC — por padrão, cobrir apenas a(s) User Story(ies) P1.** Se o usuário
pedir explicitamente para incluir P2/P3 via `$ARGUMENTS`, expandir o escopo
conforme solicitado. Deixar claro no resumo final quais User Stories foram cobertas
e quais ficaram de fora.

### 4. Gerar o protótipo

Criar a estrutura de arquivos no diretório de saída (passo 1), usando a stack
detectada (passo 2):

- Scaffold mínimo compatível com o framework do projeto (ex: componente(s) React
  funcionais cobrindo as telas identificadas)
- Dados mockados in-memory para simular as respostas de backend — **sem** chamadas a
  APIs reais
- Estados de UI cobrindo pelo menos loading, erro e sucesso quando mencionados no
  spec.md

Criar também `<output_dir>/README.md` documentando:
- Objetivo da POC e a spec de origem
- O que foi mockado (e o que precisará de integração real depois)
- Como rodar localmente
- Quais User Stories foram cobertas

### 5. Oferecer execução local

Se o scaffold gerado for um projeto Node com script de dev (`package.json` com
`dev`/`start`), perguntar ao usuário se deseja executar (`npm run dev` ou
equivalente) para revisar visualmente. Não executar automaticamente sem
confirmação.

### 6. Exibir resumo

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Porto — POC de Frontend gerada
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Stack detectada: <linguagem/framework>
User Stories cobertas: US-01, US-02 (P1)
User Stories fora do escopo: US-03 (P2)

📁 poc/<spec-name>/
   └── README.md — como rodar e o que foi mockado
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Não-objetivos

- Não é a implementação final — o `/speckit.plan` e `/speckit.tasks` continuam sendo
  necessários para a entrega real.
- Não deve tocar em código de backend ou infraestrutura de produção.
- Não deve rodar a suíte de testes do projeto principal.
