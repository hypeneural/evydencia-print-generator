# Status

**Estado em 2026-10-04:** renderer/geometria multi-produto estão avançados; menu moderno do Windows foi validado visualmente; a UI do Operador está em hardening de viewport/interação e a main atual não está com CI remoto totalmente verde.

## Evidência atual
- main auditada: `f0e2d1280f1ad347816bdcfb5b7c2446a74048bb`.
- GitHub Actions #49: verify_repo PASS, pytest Linux PASS (122 passed, 7 skipped), Ruff FAIL; workflow geral FAILURE.
- Windows contract PASS, porém o workflow atual ainda não executa pytest completo no Windows.
- Frontend ainda não possui job remoto próprio de test/build na main auditada.
- Captura real do Windows 11 Home 25H2 confirma “Gerar com EVYDÊNCIA” no menu moderno com ícone.

## Renderer / geometria
- Calendário: asset 1067×1474 e slot transparente medido correspondem ao template atual.
- Globo: output 1795×1205.
- Chaveiro: output 2551×1795.
- Render final e preview visual são contratos diferentes; UI não é considerada validada apenas pelos testes de output.

## UI Operador — HARDENING (M4 — Issue #15)
Status dos entregáveis:
- [x] PreviewLayout separado de canvas físico: PASS local (`apps/ui/src/domain/layout.ts`)
- [x] Corrigir aspect ratio visual de Globo/Chaveiro: PASS local (`apps/ui/src/domain/visual_layout.test.ts`)
- [x] Overlay do Calendário ocupar 100% do preview: PASS local (`ProductCanvas.tsx`)
- [x] Cena Fabric persistente sem reload no hot path: PASS local (`ProductCanvas.tsx`)
- [x] Startup assíncrono sem bloqueio de thumbnails: PASS local (`window.py`, `bridge.py`, `App.tsx`)
- [x] Double-click de duplicação por produto: PASS local (`duplication.ts`, `duplication.test.ts`, `App.tsx`)
- [x] Bateria de testes visuais e frontend CI: PASS local (42 testes Vitest, build Vite, CI workflow atualizado)

## Windows
- menu moderno: VISUAL PASS;
- ícone: VISUAL PASS;
- posição absoluta como primeira entrada: não controlável pela API moderna; Explorer decide agrupamento;
- lifecycle/install/uninstall/release signing continuam sujeitos aos gates da entrega correspondente.

## Regra
Não usar “100% concluído” sem listar os gates de docs/QUALITY_GATES.md.
