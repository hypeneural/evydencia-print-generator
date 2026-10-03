---
name: fabric-canvas
description: "Implementa o runtime React/Fabric.js de slots, clipping, transforms, history e layers sem acoplar o contrato ao Fabric. Use ao alterar o canvas ou interação direta da foto."
---
# Fabric Slot Runtime

Leia `apps/ui/AGENTS.md`, `docs/EDITOR_UX.md` e use /editor-performance em interação de alta frequência.

## Modelo
- Template define geometria/layers.
- Job define source + pan/zoom/rotação por slot.
- SourceRegistry fornece preview decodificado.
- FabricObject é apenas projeção desses três estados.

## Transformação persistida
Por slot:
- `pan_x_norm`
- `pan_y_norm`
- `scale` relativo ao cover mínimo
- `rotation_deg`
- `source_id`

Nunca persistir left/top/scaleX/angle bruto do Fabric como contrato.

## Crop/adjust
1. compute cover mínimo;
2. `scale=1` = cover;
3. aplicar pan em coordenada normalizada;
4. clamp para não revelar vazio quando cover_required;
5. rotação recalcula limites/clamp;
6. commit Job ao fim do gesto.

## History
- uma interação contínua = uma entrada;
- snapshot apenas de state pequeno, nunca pixels;
- undo/redo precisa restaurar source/transform/layer action de forma determinística.

## Layers
Operador: slot/background/overlay seguem Template, sem reordenação estrutural.
Gestor: reordenação/lock/visibility permitidos dentro das regras do template.

## Testes
round-trip, resize sem drift, cover/clamp, rotação, history, source reuse, seleção e layer lock.
