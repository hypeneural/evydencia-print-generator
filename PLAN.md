# Plano de Implementação

Ordem: contratos → matemática → render → editor → produtos → gestor → Windows/installer → hardening.

## Fase 0 — Bootstrap e governança
- [x] Auditoria oficial AntiGravity 2.19.1.
- [x] Root AGENTS enxuto + regras por diretório.
- [x] Agente principal + 5 especialistas.
- [x] Skills progressivas; workflows novos proibidos.
- [x] Hook pós-escrita para validar customizações.
- [x] Schemas Template/Job v1.
- [x] Validadores mecânicos + CI Linux/Windows.
- [x] Templates draft dos 3 produtos.

## Fase 1 — Contratos e geometria
- [x] Helper canônico mm→px + testes.
- [ ] Confirmar DPI de produção.
- [ ] Confirmar Chaveiro em prova física e pareamento frente/verso.
- [ ] Confirmar geometria do Calendário.
- [ ] Confirmar X/Y do Globo.
- [ ] Fechar naming/collision policy.

## Fase 2 — Renderer
- [ ] EXIF transpose.
- [ ] cover/crop/pan/zoom/rotação.
- [ ] clipping e overlay RGBA.
- [ ] output atômico/collision-safe.
- [ ] golden tests.

## Fase 3 — Calendário MVP
- [ ] React/Vite/Fabric.
- [ ] pywebview bundle local.
- [ ] Job round-trip.
- [ ] render Pillow.

## Fase 4 — Chaveiro
- [ ] quantidade 1–9.
- [ ] preencher quantidade/folha.
- [ ] overrides individuais.

## Fase 5 — Globo
- [ ] dois slots independentes/duplicáveis.

## Fase 6 — Gestor
- [ ] editor visual de canvas/slots/grupos/overlay.
- [ ] validação + publish/version.

## Fase 7 — Windows
- [ ] CLI launch contract.
- [ ] PyInstaller.
- [ ] Inno Setup + classic shell verb.
- [ ] matriz Win10/11.
- [ ] avaliar IExplorerCommand/MSIX.

## Fase 8 — Hardening
- [ ] benchmark.
- [ ] deps/licenças/security.
- [ ] assinatura quando aplicável.
