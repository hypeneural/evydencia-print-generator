---
name: editor-performance
description: "Perfila e otimiza responsividade, Fabric.js, image previews, history e memória do editor. Use quando adicionar interação de alta frequência, muitos slots, zoom/drag, resize de janela ou investigar jank."
---
# Editor Performance

Leia `docs/PERFORMANCE_BUDGETS.md`. Para detalhes Fabric, consulte `resources/fabric-performance.md`.

## Decision tree
- Jank durante pointermove/wheel? → profile primeiro; elimine alocação/decode/state global; agrupe por requestAnimationFrame.
- Jank ao abrir produto? → medir ingest/preview e construção do canvas separadamente.
- Memória alta? → confirme se original ou previews duplicados estão no JS heap.
- Zoom da foto lento? → não usar viewport zoom como substituto; revisar cache e frequência de render.
- Muitos updates React? → estado efêmero de gesture fica perto do canvas; commit ao domínio no fim do gesto.

## Guardrails
- Um preview decodificado por source, não por slot.
- Não recriar clipPath/objects em pointermove.
- Coalescer wheel/slider/history.
- Evitar setState global a cada frame.
- Batch add/remove/update e uma render request ao final.
- Configuração Fabric de cache só muda com benchmark antes/depois.

## Evidência
Registre máquina, foto(s), número de slots, resolução da janela, cenário e p50/p95. Não aceite "parece rápido" como benchmark.
