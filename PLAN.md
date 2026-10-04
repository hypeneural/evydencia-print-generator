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

## Fase 3 — Operator UI Hardening — PRÓXIMO
- [ ] corrigir CI/lint e adicionar frontend + pytest Windows no GitHub Actions.
- [ ] PreviewLayout independente de resolução de produção.
- [ ] aspect ratio visual exato para os três produtos.
- [ ] cena Fabric persistente.
- [ ] remover decode/fromURL/clear do hot path.
- [ ] startup assíncrono sem bloquear thumbnail.
- [ ] overlay Calendário 100% + cover inicial.
- [ ] double-click Chaveiro/Globo preservando transform.
- [ ] teste visual de switching/resize/overlay.
- [ ] benchmark de drag/zoom.

## Fase 4 — Modo Gestor / Template schema 1.1
- [ ] layers/background/assets.
- [ ] bring forward/send backward.
- [ ] lock/visibility.
- [ ] criar/redimensionar slot.
- [ ] guides/snap.
- [ ] groups/regras.
- [ ] validate/publish/version.

## Fase 5 — Release hardening
- [ ] ICC/lab physical validation.
- [ ] deps/licenças/security.
- [ ] assinatura release executable/MSIX/installer.
- [ ] install/update/uninstall matrix.
- [ ] branch protection/checks obrigatórios.
