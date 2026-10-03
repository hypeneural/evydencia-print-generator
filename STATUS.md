# Status

**Estado:** Fundação pronta; próximo marco é o vertical slice do editor Calendário.

## Infra concluída
- AntiGravity 2.19.1 auditado em 2026-10-03.
- `evydencia-builder` + especialistas de produto, UX, Fabric, render, Windows e QA.
- Rules/Skills/Hooks com validação mecânica.
- Schemas Template/Job v1.
- Templates draft: Chaveiro, Calendário, Globo.
- Python package mínimo + mm→px.
- CI Linux + Windows verde.

## Auditoria de editor adicionada
- UX separada em Operador/Gestor.
- Ingest unificado: context menu, dialog e drag/drop.
- preview proxy desacoplado do original.
- budgets de performance.
- pipeline EXIF/ICC/DPI/JPEG documentado.
- Fabric 7.4.0, pywebview 6.2.1 e Pillow 12.x validados contra docs atuais.

## Bloqueios físicos
- DPI de produção;
- geometria física do Calendário;
- X/Y do Globo;
- prova física/margens/pareamento do Chaveiro;
- política ICC/profile do laboratório;
- naming final.

## Próximo passo executável
Implementar `docs/EDITOR_IMPLEMENTATION_PLAN.md` E1 + E2:
1. SourceRegistry/preview pipeline;
2. renderer determinístico;
3. só então UI Calendário com Fabric.

Não iniciar o modo Gestor completo antes de provar preview/render parity no Calendário.
