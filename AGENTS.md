# EVYDÊNCIA Print Generator — Workspace Contract

Este arquivo é propositalmente curto porque fica sempre ativo. Regras específicas vivem em AGENTS.md por diretório, .agents/rules/ e Skills carregadas sob demanda.

## Missão
Construir um aplicativo Windows local, simples para o operador e configurável pelo gestor, para gerar Calendário, Chaveiro e Globo a partir de um único motor orientado a templates e slots.

## Invariantes
1. Um motor, vários templates.
2. Milímetros são a unidade física canônica; pixels derivam do DPI.
3. Preview não é render final; o render reaplica o Job sobre a foto original.
4. Template define produto; Job define uma execução.
5. Nunca sobrescrever a fotografia original.
6. Nunca versionar fotos reais de clientes, familiares ou crianças.
7. V1 é local/offline, sem servidor externo ou banco obrigatório.
8. Não inventar medidas: desconhecido = draft/TBD.
9. Mudança incompatível exige schema version + ADR + testes/migração.
10. O menu de contexto apenas lança o app; processamento não roda dentro do Explorer.

## Stack aprovada
React + TypeScript + Fabric.js; Python + pywebview + Pillow; JSON Schema; PyInstaller + Inno Setup.

## Fluxo AntiGravity 2.19.1
- Para tarefa não trivial, prefira o /plan nativo antes de escrever código.
- Use o agente principal `evydencia-builder` para trabalho de produto/repositório.
- Delegue por domínio: product-architect, canvas-engineer, render-engineer, windows-engineer, quality-auditor.
- Pesquisa paralela pode compartilhar workspace; implementações independentes preferem branch/worktree.
- Nunca deixe dois subagentes editando os mesmos arquivos em paralelo.
- O 2.19.1 permite conversar diretamente com um subagente; use isso para esclarecer achados sem poluir o agente principal.
- Antes de concluir, rode `python scripts/verify_repo.py`, testes e lints relevantes.

## Documentos de entrada
- @PLAN.md
- @STATUS.md
- @docs/ARCHITECTURE.md
- @docs/PRODUCT_SPECS.md
- @docs/ANTIGRAVITY.md

## Regras por área
- apps/ui/AGENTS.md
- apps/desktop/AGENTS.md
- templates/AGENTS.md
- schemas/AGENTS.md
- installer/AGENTS.md
- tests/AGENTS.md
