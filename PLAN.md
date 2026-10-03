# Plano de Implementação

Sequência: contratos → matemática → render → editor → produtos → gestor → Windows/installer → hardening.

## Fase 0 — Bootstrap
- [x] Auditoria Antigravity 2.19.1.
- [x] Root AGENTS enxuto + regras por diretório.
- [x] Custom agents com model/policy/skills.
- [x] Skills progressivas; zero workflows novos.
- [x] Auditoria Fabric.js/editores/pywebview/PowerToys.
- [x] Specs conhecidos dos três produtos.
- [ ] Validar CI remoto após publicação.

## Fase 1 — Contratos e geometria
- [ ] Fechar template.schema.json v1 e job.schema.json v1.
- [ ] Helper canônico mm↔px + testes.
- [ ] Validação draft vs production.
- [ ] Testar Chaveiro 216×152, 34×44, 6×3 e centralização derivada.
- [ ] Confirmar pareamento/margens em prova física.

## Fase 2 — Render
- [ ] API render(template, job).
- [ ] EXIF transpose.
- [ ] cover/crop, pan, zoom e rotação.
- [ ] clipping e overlay RGBA.
- [ ] output collision-safe/atômico.
- [ ] golden tests.

## Fase 3 — Calendário MVP
- [ ] React/Vite/Fabric e lockfile.
- [ ] pywebview com bundle local.
- [ ] foto sob overlay travado.
- [ ] pan/zoom/rotação/reset.
- [ ] Job round-trip UI↔Python.
- [ ] render final Pillow.

## Fase 4 — Chaveiro
- [ ] 18 slots.
- [ ] quantidade 1–9, 2 slots/unidade.
- [ ] preencher quantidade / preencher folha.
- [ ] override individual.

## Fase 5 — Globo
- [ ] confirmar X/Y dos 2 slots 50×80 mm.
- [ ] fontes independentes/duplicação.

## Fase 6 — Modo Gestor
- [ ] editar canvas/slots/grupos/overlay/permissões.
- [ ] snap/guias sem usar JSON Fabric como contrato.
- [ ] validação/publicação/versionamento.

## Fase 7 — Windows
- [ ] contrato CLI.
- [ ] PyInstaller.
- [ ] Inno Setup.
- [ ] shell verb via HKA\Software\Classes.
- [ ] teste Windows 10/11, Unicode, espaços, caminho longo, uninstall.
- [ ] avaliar IExplorerCommand/MSIX pós-MVP.

## Fase 8 — Hardening
- [ ] CI Linux + Windows completo.
- [ ] benchmark com fotos de câmera.
- [ ] auditoria deps/licenças/security.
- [ ] assinatura de executável quando necessário.
