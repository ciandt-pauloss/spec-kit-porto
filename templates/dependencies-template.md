# Matriz de Dependências: [FEATURE NAME]

**Feature**: `[###-feature-name]`
**Criado em**: [DATE]
**Spec de origem**: `specs/[###-feature-name]/spec.md`

**Nota**: Este artefato é gerado pelo comando `/speckit.porto.dependencies`. Ele mapeia
as dependências externas ao time responsável pela feature — outros times/verticais da
Porto, APIs, componentes compartilhados ou infraestrutura de terceiros necessários para
a entrega. Uma versão em planilha (`dependencies.xlsx`) é gerada com o mesmo conteúdo
desta tabela.

<!--
  AÇÃO NECESSÁRIA: as linhas da tabela abaixo são exemplos ilustrativos.
  O comando /speckit.porto.dependencies DEVE substituí-las pelas dependências
  reais identificadas no spec.md e demais artefatos da feature.
-->

## Dependências Identificadas

| Tipo | Vertical / Departamento | Responsável | Nome | Descrição |
|------|--------------------------|--------------|------|-----------|
| API | [Departamento Porto, ex: Plataforma de Pagamentos] | [Time ou pessoa responsável] | [Nome da API/serviço] | [O que é consumido e por quê] |
| Infraestrutura | [Departamento] | [Responsável] | [Nome do recurso] | [Descrição do uso] |
| Componente | [Departamento] | [Responsável] | [Nome do componente/design system] | [Descrição do uso] |
| Serviço Externo | [Departamento ou "Terceiro"] | [Responsável] | [Nome do fornecedor/serviço] | [Descrição do uso] |

## Itens Pendentes de Esclarecimento

<!--
  Listar aqui toda dependência cujo Responsável, Vertical ou Nome não puderam ser
  determinados com confiança a partir do spec.md — mantendo o marcador
  NEEDS CLARIFICATION para ficar consistente com o restante da spec.
-->

- [ ] [NEEDS CLARIFICATION: descrição do que falta esclarecer]

## Notas

- Esta matriz deve ser revisada com os responsáveis de cada vertical antes do `/speckit.plan`,
  para que restrições e prazos de terceiros entrem no planejamento.
- Novas dependências identificadas durante o planejamento ou implementação devem ser
  adicionadas manualmente aqui e refletidas na planilha correspondente.
