# Status

**Estado em 2026-10-04:** M4 (Operator UI Hardening) e M5-A (Manager Mode Foundation) concluídos e mergeados na `main`. O PR #20 está em hardening forense antes dos gates de validação visual e manual no Windows 11. O PR #19 permanece bloqueado.

## Evidência atual
- main base auditada: `7a6966b098fd728707e4f2d02621372d61da80ba`.
- CI na main: 100% verde (Run #37245385949).
- PR #20 (`fix/product-preview-viewport-and-drop-ux`): Push Run #37253314308 e PR Run #37253348995 100% verdes (HEAD `cc2499c41d11e613c164f6eeb8dac3e81f175f32`).
- Status do PR #20: BLOCKED — FORENSIC HARDENING REQUIRED (G4 Visual, G5 Performance, G6 Windows Native Drop e G7 Physical Geometry em PENDING).
- Branch stacked `feat/operator-batch-assignment-delete` (PR #21, base PR #20):
  - G1 Repository: PASS
  - G2 Unit/Contract: PASS (243 testes Vitest em 10 suites / 141 testes Pytest)
  - G3 Remote CI: PASS (PR #21, Runs #37267085333 e #37267099247 100% verdes)
  - Veredito: READY_FOR_VISUAL_REVIEW (bloqueada para merge até que o PR #20 seja finalizado e mergeado na main).
- Branch stacked `feat/operator-precision-polaroid-partial-render` (PR #22, base PR #21):
  - G1 Repository: PASS
  - G2 Unit/Contract: PASS (260 testes Vitest em 11 suites / 152 testes Pytest Windows / 143 passed + 9 skipped Linux)
  - G3 Remote CI: PASS (PR #22, Run #37273065455 100% verde)
  - G4 UI / Visual: PENDING
  - G5 Performance: PENDING
  - G6 Windows Shell / Explorer Reveal: PASS (64-bit ctypes + fallback)
  - G7 Physical Geometry: PENDING (Polaroid em draft aguardando prova física)
  - Veredito: READY_FOR_VISUAL_REVIEW
- Branch stacked `feat/ui-branding-accessibility-governance` (base PR #22):
  - G1 Repository: PASS
  - G2 Unit/Contract: IN PROGRESS
  - G3 Remote CI: PENDING
  - G4 UI / Visual: PENDING
  - G5 Performance: PENDING
  - G6 Windows Shell Integration: PASS
  - G7 Physical Geometry: PENDING (Template Governance Audit em andamento)
  - Veredito: WORK_IN_PROGRESS
- PR #19 (`feat/manager-publish-pipeline`): BLOQUEADO até que o PR #20 seja finalizado e mergeado.

## Renderer / geometria
- Calendário: asset 1067×1474 a 254 DPI e slot medido correspondem ao template atual.
- Globo: output canônico 1795×1205 a 300 DPI (`152×102 mm`, layout assimétrico derivado de gabarito real, `template_version: 1.1.0`).
- Chaveiro: output 2551×1795 a 300 DPI (`216×152 mm`, 18 slots em 6×3, suporte a renderização parcial a partir de 2 slots).
- Polaroid Natal: output 980×1205 a 300 DPI (`82.97×102.02 mm`, 1 slot medido `foto_principal`, overlay obrigatório fail-closed, template draft).
- Render final e preview visual são contratos separados; UI não é validada apenas pelos testes de render.

## Marcos
- M4 (Operator UI Hardening): **MERGED** (PR #16, Issue #15 fechada).
- M5-A (Manager Mode Foundation): **MERGED** (PR #18).
- PR #20 (Hotfix / Viewport, Wheel coalescido, Explorer DnD, Globo v1.1.0 e Paridade Visual Fabric 7): **EM HARDENING FORENSE**.
- PR #21 (`feat/operator-batch-assignment-delete`): **READY_FOR_VISUAL_REVIEW**.
- PR Stacked (`feat/operator-precision-polaroid-partial-render`): **READY_FOR_VISUAL_REVIEW** (Rotação fina, Shift multi-selection, duplicação em lote, Polaroid Natal draft, Explorer auto-reveal, Chaveiro parcial >= 2 slots, fail-closed overlay check).
- M5-B (Persistência e versionamento do Gestor): **PENDENTE** (inicia após conclusão deste ciclo).

## Regra
Não usar “100% concluído” sem listar os gates de docs/QUALITY_GATES.md.
