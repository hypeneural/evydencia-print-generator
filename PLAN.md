# Plano de Implementação

Estratégia: vertical slice funcional antes de generalizar. Ver `docs/EDITOR_IMPLEMENTATION_PLAN.md`.

## Fase 0 — Bootstrap/governança
- [x] AntiGravity 2.19.1 validado contra docs oficiais.
- [x] Root AGENTS curto + regras por diretório.
- [x] Coordenador + especialistas.
- [x] Skills progressivas; zero workflows novos.
- [x] Hook/validators + CI Linux/Windows.
- [x] Template/Job schema v1 + templates draft.
- [x] Repository Map para reduzir exploração.
- [x] Arquitetura profissional do menu Windows documentada.

## Fase 1 — Editor foundation (M1 Concluído)
- [x] SourceRegistry.
- [x] Ingest único para CLI/dialog/drop.
- [x] preview proxy cache 2048px + dedupe.
- [x] benchmark baseline na máquina Windows 11 Home 25H2.
- [x] renderer EXIF/cover/pan/zoom/rotate/clip.
- [x] alpha overlay.
- [x] JPEG/PNG quality/DPI/collision policy.
- [x] golden tests.
- [x] confirmar color policy/lab profile.

## Fase 2 — Calendário vertical slice (M1 Concluído)
- [x] React/Vite/Fabric shell.
- [x] source tray.
- [x] slot editável.
- [x] overlay bloqueado.
- [x] history command stack.
- [x] Job round-trip.
- [x] Generate → Pillow.
- [x] preview/render parity.
- [x] performance gate.

## Fase 3 — Windows 11 professional shell
- [ ] contrato CLI estável.
- [ ] `native/windows-shell` C++20 x64.
- [ ] IExplorerCommand.
- [ ] sparse MSIX.
- [ ] signing de desenvolvimento.
- [ ] menu moderno real no Windows 11 Home 25H2.
- [ ] classic fallback per-user.
- [ ] installer install/update/uninstall.
- [ ] signed CI/release strategy.
- [ ] multi-select depois do single-select estável.

## Fase 4 — Chaveiro (M2 Concluído)
- [x] 18 slots.
- [x] grade 6x3 em folha 216x152 mm a 300 DPI.
- [x] fill sheet ("Preencher todos os 18 slots").
- [x] overrides individuais de foto e transform por slot.
- [x] linhas de refile de 1px geradas para guilhotina.

## Fase 5 — Globo (M2 Concluído)
- [x] geometria X/Y confirmada (2 slots 50x80 mm em 152x102 mm a 300 DPI).
- [x] 2 slots independentes e simétricos com gap 7 mm.
- [x] duplicate same source ("Usar mesma foto nos dois").
- [x] linhas de refile de 1px geradas para corte.

## Fase 6 — Gestor / Template schema 1.1
- [ ] layers/background/assets.
- [ ] bring forward/send backward.
- [ ] lock/visibility.
- [ ] criar/redimensionar slot.
- [ ] guides/snap.
- [ ] groups/regras.
- [ ] validate/publish/version.

## Fase 7 — Hardening
- [ ] benchmarks e memory profiles.
- [ ] ICC/lab physical output validation.
- [ ] deps/licenças/security.
- [ ] assinatura de executable/installer/release.
