# Plano de Implementação

Estratégia atual: vertical slice funcional antes de generalizar. Ver `docs/EDITOR_IMPLEMENTATION_PLAN.md`.

## Fase 0 — Bootstrap/governança
- [x] AntiGravity 2.19.1 validado contra docs oficiais.
- [x] Root AGENTS curto + regras por diretório.
- [x] `evydencia-builder` + especialistas.
- [x] Skills progressivas; zero workflows novos.
- [x] Hook/validators + CI Linux/Windows.
- [x] Template/Job schema v1 + templates draft.

## Fase 1 — Editor foundation
- [ ] SourceRegistry.
- [ ] Ingest único para CLI/dialog/drop.
- [ ] preview proxy cache 2048px + dedupe.
- [ ] benchmark baseline Windows.
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

## Fase 3 — Chaveiro
- [ ] 18 slots.
- [ ] quantidade 1–9.
- [ ] fill quantity/fill sheet.
- [ ] overrides individuais.
- [ ] confirmar pareamento/margens em prova física.

## Fase 4 — Globo
- [ ] confirmar X/Y;
- [ ] 2 slots independentes;
- [ ] duplicate same source.

## Fase 5 — Gestor / Template schema 1.1
- [ ] layers/background/assets;
- [ ] bring forward/send backward;
- [ ] lock/visibility;
- [ ] criar/redimensionar slot;
- [ ] guides/snap;
- [ ] groups/regras;
- [ ] validate/publish/version.

## Fase 6 — Windows
- [ ] CLI launch real;
- [ ] PyInstaller;
- [ ] Inno Setup;
- [ ] context menu clássico;
- [ ] matriz Win10/11;
- [ ] multi-select somente após V1 estável;
- [ ] avaliar IExplorerCommand/MSIX.

## Fase 7 — Hardening
- [ ] benchmarks e memory profiles;
- [ ] ICC/lab physical output validation;
- [ ] deps/licenças/security;
- [ ] assinatura de executável se necessário.
