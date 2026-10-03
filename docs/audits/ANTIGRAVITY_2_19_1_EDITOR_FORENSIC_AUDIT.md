# Auditoria Forense — AntiGravity 2.19.1 + Editor Architecture

**Data:** 2026-10-03

## Fontes oficiais AntiGravity
- Changelog: https://www.antigravity.google/docs/changelog
- Rules: https://www.antigravity.google/docs/rules/
- Skills: https://www.antigravity.google/docs/skills
- Custom subagents: https://www.antigravity.google/docs/subagents
- Slash commands/plan: https://www.antigravity.google/docs/slash-commands/

## Fatos 2.19.1
A documentação oficial marca v2.19.1 como Latest em 2026-09-30. A release permite mensagem direta a subagentes e corrige custom agents que ignoravam rules globais/projeto.

v2.18.1 tornou budget de customizações visível e corrigiu worktrees de subagentes. v2.17 introduziu /plan, hooks por custom agent, budget próprio de rules e /.gemini/config.json.

## Achados no repo antes desta revisão

### E-A01 — governança boa, mas pouco orientada ao editor real — HIGH
Agents falavam de Fabric/Pillow, mas não definiam SourceRegistry, preview proxy, history, UX Operador/Gestor ou performance budgets.

**Correção:** novos skills e docs de editor/ingest/performance/quality; prompts dos agentes atualizados.

### E-A02 — risco de carregar JPEG full-res no Fabric — HIGH
Sem regra explícita, uma implementação natural poderia colocar originais de ~8 MB diretamente no browser, multiplicando memória após decode.

**Correção:** invariant "preview no Fabric, original no renderer"; SourceRegistry + proxy 2048px.

### E-A03 — UX do Gestor misturada com Operador — HIGH
"Layers/forward/back" poderia transformar o Operador em editor genérico.

**Correção:** dois modos. Operador edita conteúdo dentro de slots; Gestor edita estrutura/layer order.

### E-A04 — ausência de history architecture — MEDIUM
Editor profissional precisa undo/redo, mas snapshots Fabric/pixels são pesados e frágeis.

**Correção:** command history de domínio, coalescendo uma interação contínua em uma entrada.

### E-A05 — três portas de ingest não convergiam — MEDIUM
Context menu estava previsto, mas file dialog e drag/drop não tinham contrato comum.

**Correção:** pywebview atual suporta multi-file dialog e full path em Python-side drop; todos convergem ao IngestService.

### E-A06 — qualidade não tinha política suficiente — HIGH
EXIF era citado, mas ICC/DPI/JPEG/subsampling e encode único não estavam formalizados.

**Correção:** skill image-quality + IMAGE_PIPELINE. Pillow docs confirmam EXIF transpose, LANCZOS, ICC/DPI e recomendam evitar JPEG quality >95.

### E-A07 — otimização sem budget/medição — MEDIUM
Fabric tem caching útil, mas o guia oficial também descreve overhead e viewport zoom como hotspot com muitos objetos.

**Correção:** performance budget + skill com decisão orientada a profiling; sem alterar cache global por intuição.

## Fontes técnicas
- Fabric 7.4.0: https://github.com/fabricjs/fabric.js/releases
- Fabric caching: https://www.fabricjs.com/docs/fabric-object-caching/
- pywebview API/drop: https://pywebview.flowrl.com/api/ e /examples/drag_drop
- Pillow concepts/formats: https://pillow.readthedocs.io/

## Decisão de próximo marco
Implementar E1 SourceRegistry/preview + E2 Renderer, então E3 Calendário. O modo Gestor completo é deliberadamente adiado até o núcleo provar paridade visual, performance e qualidade.
