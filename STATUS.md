# Status

**Estado:** Fase 0 concluída e validada remotamente; Fase 1 parcialmente iniciada.

## Infra concluída
- AntiGravity 2.19.1 auditado contra documentação oficial em 2026-10-03.
- `evydencia-builder` + 5 subagentes especializados.
- Root `AGENTS.md` enxuto + regras por diretório.
- 8 Skills com progressive disclosure; zero workflows legados.
- Hook pós-escrita para validar customizações.
- Schemas Template/Job v1.
- Templates draft: Chaveiro, Calendário e Globo.
- Python package mínimo + helper canônico mm→px.
- 7 ADRs materializados e indexados.
- CI Linux + Windows usando `actions/checkout@v7` e `actions/setup-python@v7`.

## Evidência remota
GitHub Actions run #16:
- commit: `b7bc07873497a01d6f10e074d1323646d9ed24bc`
- conclusion: **success**
- contracts (Ubuntu): verify_repo + pytest + Ruff = success
- windows-contract: instalação + validação AntiGravity/templates + CLI = success
- URL: https://github.com/hypeneural/evydencia-print-generator/actions/runs/37152264949

## Produto confirmado
- Chaveiro: 216×152 mm; grid 6×3; slot 34×44 mm; 2 fotos/chaveiro.
- Calendário: 1 foto sob overlay; pan/zoom/rotação.
- Globo: 152×102 mm; 2 fotos 50×80 mm.
- Entrada desejada: menu de contexto Windows e abertura direta.

## Bloqueios para templates production
- DPI final;
- geometria física do Calendário;
- X/Y do Globo;
- prova física/margens/pareamento do Chaveiro;
- naming final.

## Próximo passo
Fechar Fase 1 com dados físicos confirmados; em seguida construir o renderer Pillow antes da UI Fabric.
