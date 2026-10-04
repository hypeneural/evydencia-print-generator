---
name: fabric-canvas
description: "Implementa runtime React/Fabric.js de PreviewLayout, slots, clipping, transforms, history e overlays sem acoplar o contrato ao Fabric. Use ao alterar canvas/interação."
---
# Fabric Slot Runtime

Leia apps/ui/AGENTS.md e docs/UI_RUNTIME_ARCHITECTURE.md.

## Modelo
- Template = geometria de produção.
- PreviewLayout = geometria de tela.
- Job = source + transform normalizado.
- FabricObject = projeção efêmera.

## Viewport
Preserve aspect ratio. Não use resolução de produção gigante no layout DOM + CSS transform como única solução.
Fabric `setDimensions(..., { cssOnly: true })` existe como opção oficial; qualquer abordagem precisa manter hit-testing e Job independentes do viewport.

## Cena persistente
Reconcilie objetos por template/source; não destrua cena por pan/zoom.

Hot path:
1. obter FabricImage existente;
2. calcular placement;
3. set left/top/scale/angle;
4. requestRenderAll coalescido;
5. commit no domínio ao fim do gesto.

Proibido no hot path:
- fabric.clear();
- FabricImage.fromURL();
- decode;
- criação repetida de overlay/clipPath.

## Transform
scale=1 = cover; pan normalizado; rotação/clamp; nunca persistir propriedades brutas do Fabric.

## Events
Fabric fornece mouse:dblclick oficialmente. Semântica é do produto, conforme docs/EDITOR_UX.md.

## History
Um gesto/duplicação = uma entrada; nunca pixels.

## Testes
round-trip, resize sem drift, aspect ratio, cover/clamp, history, source reuse, switching e overlay lock.
