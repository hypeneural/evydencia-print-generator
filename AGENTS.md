# EVYDÊNCIA Print Generator — Workspace Contract

Este arquivo é deliberadamente curto: ele fica sempre ativo no escopo raiz. Detalhes de domínio vivem em AGENTS.md de subdiretórios, .agents/rules/ ou .agents/skills/.

## Missão
Construir um aplicativo desktop Windows local, confiável e simples para gerar Calendário, Chaveiro e Globo a partir de um único motor orientado a templates e slots.

## Invariantes
1. Um motor, vários templates.
2. Milímetros são a unidade física canônica; pixels são derivados do DPI.
3. Preview não é render final; o render reaplica transformações sobre o original.
4. Template define produto; Job define execução.
5. Nunca sobrescrever a foto original.
6. Não versionar fotos reais de clientes, familiares ou crianças.
7. V1 offline/local, sem servidor externo e sem banco obrigatório.
8. Não inventar medidas; dados pendentes permanecem draft/TBD.
9. Mudança incompatível exige schema version + ADR + testes.
10. O menu de contexto apenas lança o app; processamento nunca roda dentro do Explorer.

## Stack aprovada
React + TypeScript + Fabric.js; Python + pywebview + Pillow; JSON Schema; PyInstaller + Inno Setup.

## Como trabalhar
- Consulte @PLAN.md e @STATUS.md antes de mudança não trivial.
- Use a skill mais específica em .agents/skills/.
- Consulte @docs/ARCHITECTURE.md e @docs/PRODUCT_SPECS.md quando necessário.
- Para mudança transversal, use /implementation-plan.
- Mantenha lógica de domínio fora de React e fora da integração Windows.
- Não permita dois subagentes editando os mesmos arquivos em paralelo.
- Pesquisa sem escrita pode compartilhar workspace; implementações independentes preferem worktree/branch.
- Antes de concluir rode `python scripts/verify_repo.py`, testes e lints relevantes.
- Atualize STATUS.md e ADRs quando o estado/arquitetura mudar.

## Regras por área
- apps/ui/AGENTS.md
- apps/desktop/AGENTS.md
- templates/AGENTS.md
- schemas/AGENTS.md
- installer/AGENTS.md
- tests/AGENTS.md

## Subagentes
product-architect, canvas-engineer, render-engineer, windows-engineer, quality-auditor.
