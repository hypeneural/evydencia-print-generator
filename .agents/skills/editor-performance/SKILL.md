---
name: editor-performance
description: "Perfila e otimiza Fabric.js, React, previews, history, startup e memória. Use em drag/zoom/resize, muitos slots, loading ou qualquer jank."
---
# Editor Performance

Leia docs/PERFORMANCE_BUDGETS.md.

## Decision tree
- jank pointermove/wheel? -> procure rebuild/decode/setState global antes de mexer em cache;
- produto troca deformado? -> audite PreviewLayout/aspect ratio, não Template físico;
- abertura lenta? -> separar window creation de preview generation;
- memória alta? -> confirmar duplicação de preview/original;
- cache Fabric? -> profile antes/depois.

## Hot path
- cena persistente;
- refs locais para objetos;
- requestAnimationFrame/coalescing;
- commit React/domain no fim do gesto;
- uma source -> um preview reutilizável.

Não aceitar:
- FabricImage.fromURL no gesto;
- fabric.clear no gesto;
- preview por slot;
- bloqueio da janela aguardando thumbnail.

## Evidência
Máquina, janela, slots/sources, cold/warm, p50/p95 e Performance recording quando houver jank.
