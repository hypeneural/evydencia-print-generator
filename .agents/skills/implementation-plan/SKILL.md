---
name: implementation-plan
description: Cria um plano de implementação verificável antes de mudanças transversais, definindo contratos, arquivos, agentes/worktrees, testes, riscos e critérios de aceite. Use para features não triviais, refactors ou mudanças que atravessam UI, renderer e Windows.
---
# Implementation Plan

1. Leia `STATUS.md`, `PLAN.md`, `DECISIONS.md` e apenas os specs diretamente afetados.
2. Declare fatos confirmados, pendências e hipóteses separadamente.
3. Liste contratos que mudam (Template, Job, bridge, CLI, installer).
4. Decomponha em incrementos pequenos com ordem de dependência.
5. Marque tarefas independentes que podem ir para subagentes/worktrees separados.
6. Defina, antes do código, testes unitários, integração, golden/visual e Windows quando aplicável.
7. Identifique ADR necessário, migração de schema e impacto de distribuição.
8. Termine com critérios de aceite observáveis e comandos de validação.

Não escreva código durante esta skill, salvo se o usuário pedir explicitamente plano + implementação no mesmo turno.
