# Plano de Implementação

Estratégia: fatias testáveis + gates objetivos.

## Fase 0 — Fundação
- [x] Template/Job schemas.
- [x] SourceRegistry/ingest/preview.
- [x] renderer determinístico.
- [x] customizações AntiGravity com Rules/Skills/subagentes.
- [x] arquitetura Windows moderna.

## Fase 1 — Produção de imagem
- [x] Calendário renderer/overlay.
- [x] Globo renderer.
- [x] Chaveiro renderer.
- [x] transform normalizado e paridade geométrica.

## Fase 2 — Windows
- [x] IExplorerCommand.
- [x] sparse MSIX/dev signing.
- [x] comando visível no menu moderno Windows 11 Home 25H2.
- [x] ícone dedicado.
- [ ] manter lifecycle/release signing cobertos quando entrar em release formal.

## Fase 3 — Operator UI Hardening (M4) — CONCLUÍDO & MERGED
- [x] corrigir CI/lint e adicionar frontend + pytest Windows no GitHub Actions (PR #16).
- [x] PreviewLayout independente de resolução de produção.
- [x] aspect ratio visual exato para os três produtos.
- [x] cena Fabric persistente.
- [x] remover decode/fromURL/clear do hot path.
- [x] startup assíncrono sem bloquear thumbnail.
- [x] overlay Calendário 100% + cover inicial.
- [x] double-click Chaveiro/Globo preservando transform.
- [x] teste visual de switching/resize/overlay.
- [x] benchmark de drag/zoom.

## Hotfix PR #20 — Viewport Transform, Coalesced Wheel, Native DnD, Globo v1.1.0 & Paridade Visual Fabric 7 — EM HARDENING
- [x] migração para Fabric 7 `viewportTransform` (`[fitScale, 0, 0, fitScale, 0, 0]`).
- [x] restauração do Globo canônico 152×102 mm assimétrico derivado de gabarito real (`template_version: "1.1.0"`).
- [x] paridade visual Fabric 7: `originX: "left", originY: "top"` explícitos em rects e clipPaths (correção de cover no Calendário e alinhamento do Chaveiro).
- [x] proteção de geometria fixa de produção (`geometryLocked`) em modo Gestor e Operador.
- [x] native Explorer drag-and-drop sem bloqueio síncrono.
- [x] wheel zoom restrito a foto preenchida com hot path coalescido (zero React setState por tick).
- [x] uniform scale e guarda de aspect ratio no overlay do Calendário.
- [ ] validação visual (G4), medição de performance (G5) e teste manual no Windows 11 (G6).

## Fase 4-A — Modo Gestor Fundação (M5-A) — CONCLUÍDO & MERGED
- [x] alternância de modo `[ Operador | Gestor ]` no cabeçalho (PR #18).
- [x] Shared Editor Runtime (`ProductCanvas.tsx` unificado).
- [x] manipulação de slots estritamente em milímetros (`draft.ts`).
- [x] domínio imutável e testes unitários Vitest.

## Fase 4-B — Modo Gestor Persistência & Publicação (M5-B) — PRÓXIMO
- [ ] layers/background/assets.
- [ ] bring forward/send backward.
- [ ] lock/visibility.
- [ ] criar/redimensionar slot via UI.
- [ ] guides/snap.
- [ ] groups/regras.
- [ ] validate/publish/version atômico em disco (UserTemplateStore).

## Fase 5 — Release hardening
- [ ] ICC/lab physical validation.
- [ ] deps/licenças/security.
- [ ] assinatura release executable/MSIX/installer.
- [ ] install/update/uninstall matrix.
- [ ] branch protection/checks obrigatórios.
