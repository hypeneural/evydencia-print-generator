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

## Fase 1 — Editor foundation
- [ ] SourceRegistry.
- [ ] Ingest único para CLI/dialog/drop.
- [ ] preview proxy cache 2048px + dedupe.
- [ ] benchmark baseline na máquina Windows 11 Home 25H2.
- [ ] renderer EXIF/cover/pan/zoom/rotate/clip.
- [ ] alpha overlay.
- [ ] JPEG/PNG quality/DPI/collision policy.
- [ ] golden tests.
- [ ] confirmar color policy/lab profile.

## Fase 2 — Calendário vertical slice
- [ ] React/Vite/Fabric shell.
- [ ] source tray.
- [ ] slot editável.
- [ ] overlay bloqueado.
- [ ] history command stack.
- [ ] Job round-trip.
- [ ] Generate → Pillow.
- [ ] preview/render parity.
- [ ] performance gate.

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

## Fase 4 — Chaveiro
- [ ] 18 slots.
- [ ] quantidade 1–9.
- [ ] fill quantity/fill sheet.
- [ ] overrides individuais.
- [ ] confirmar pareamento/margens em prova física.

## Fase 5 — Globo
- [ ] confirmar X/Y.
- [ ] 2 slots independentes.
- [ ] duplicate same source.

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
