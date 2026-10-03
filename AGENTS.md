# EVYDÊNCIA Print Generator — Workspace Contract

Este arquivo é curto por design: fica always-on. Detalhes ficam em AGENTS.md por diretório, Rules condicionais e Skills carregadas sob demanda.

## Missão do produto
Criar um editor desktop Windows profissional, porém simples, para gerar Calendário, Chaveiro e Globo com qualidade de impressão. O operador deve conseguir trabalhar sem conhecer pixels, DPI, camadas ou JSON; o gestor configura templates visualmente.

## Invariantes
1. Um motor, vários templates.
2. Milímetros são a geometria física canônica; pixels derivam do DPI.
3. A foto original nunca entra no Fabric como fonte de produção: a UI usa preview/proxy; o renderer usa o original.
4. Preview não é render final. A saída é refeita em Python/Pillow.
5. Template define produto; Job define a execução.
6. Nunca sobrescrever a foto original.
7. Nunca versionar fotos reais de clientes, familiares ou crianças.
8. V1 é local/offline; nenhum upload externo é necessário.
9. Não inventar medidas: desconhecido = draft/TBD.
10. Mudança incompatível exige schema version + ADR + testes/migração.
11. Explorer só inicia o app; processamento não roda dentro de explorer.exe.
12. Simplicidade do operador vence flexibilidade genérica. Recursos avançados pertencem ao modo Gestor.

## Stack aprovada
React + TypeScript + Fabric.js 7.x; Python + pywebview 6.x + Pillow 12.x; JSON Schema; PyInstaller + Inno Setup.

## Fluxo de desenvolvimento com AntiGravity 2.19.1
- Feature transversal, arquitetura ou mudança de contrato: use /plan.
- Requisito ambíguo de UX, impressão ou produto: use /grill-me antes do código.
- Bug difícil de geometria/render/performance: /boost é apropriado quando disponível.
- UI pronta para inspeção: use /browser no servidor Vite para validar fluxo e screenshots sintéticas.
- Correção recorrente que merece persistência: use /learn e revise o diff gerado.
- Use `evydencia-builder` como coordenador e delegue ao especialista correto.
- Paralelize pesquisa/testes; não deixe dois agentes editarem os mesmos arquivos.
- Antes de concluir: `python scripts/verify_repo.py`, testes e lints relevantes.

## Documentos de entrada
- @PLAN.md
- @STATUS.md
- @docs/ARCHITECTURE.md
- @docs/EDITOR_UX.md
- @docs/IMAGE_PIPELINE.md
- @docs/PERFORMANCE_BUDGETS.md
- @docs/PRODUCT_SPECS.md
- @docs/ANTIGRAVITY.md

## Regras por área
- apps/ui/AGENTS.md
- apps/desktop/AGENTS.md
- templates/AGENTS.md
- schemas/AGENTS.md
- installer/AGENTS.md
- tests/AGENTS.md
