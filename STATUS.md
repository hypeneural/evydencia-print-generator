# Status

**Estado:** Fase 0 concluída; Fase 1 parcialmente iniciada.

## Infra concluída
- AntiGravity 2.19.1 auditado contra docs oficiais.
- evydencia-builder + 5 subagentes especializados.
- Rules/Skills/Hooks com validação mecânica.
- Schemas Template/Job v1.
- Templates draft: Chaveiro, Calendário, Globo.
- Python package mínimo + helper mm→px.
- CI Linux e Windows.

## Produto confirmado
- Chaveiro: 216×152 mm; grid 6×3; slot 34×44 mm; 2 fotos/chaveiro.
- Calendário: 1 foto sob overlay; pan/zoom/rotação.
- Globo: 152×102 mm; 2 fotos 50×80 mm.
- Entrada desejada: menu de contexto Windows e abertura direta.

## Bloqueios para production templates
- DPI final;
- geometria física do Calendário;
- X/Y do Globo;
- prova física/margens/pareamento do Chaveiro;
- naming final.

## Próximo passo
Fechar Fase 1 com os dados físicos; depois iniciar renderer Pillow antes da UI Fabric.
