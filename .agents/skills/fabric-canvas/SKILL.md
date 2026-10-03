---
name: fabric-canvas
description: Implementa ou revisa o editor React/Fabric.js de slots, clipping, pan, zoom, rotação, substituição de foto e serialização normalizada. Use em qualquer mudança do canvas Operador/Gestor.
---
# Fabric Slot Editor

## Contrato
- Fabric.js é runtime visual; Template/Job são a fonte de verdade persistente.
- O canvas de preview nunca gera o arquivo final de produção.
- Cada slot tem região fixa e foto transformável dentro de clip próprio.

## Transformação persistida
Persistir por slot, no Job:
- `pan_x_norm`
- `pan_y_norm`
- `scale` relativo ao cover mínimo
- `rotation_deg`
- `source_id`/arquivo lógico

Nunca persistir left/top/scaleX do Fabric como contrato público.

## Regras de interação
1. Calcule primeiro o `cover` mínimo.
2. `scale >= 1.0` significa multiplicador sobre esse cover.
3. Restrinja pan/zoom/rotação para `cover_required=true` não revelar fundo.
4. Resize da janela recalcula projeção visual, não transforma o Job.
5. Overlay de produto fica non-selectable no modo Operador.
6. Substituir foto mantém ou reseta transformação conforme regra explícita do produto; nunca por acidente.

## Gestor
- Expor apenas canvas físico, slots, grupos, overlay, permissões e naming.
- Usar snap/guias como auxílio, mas salvar mm no Template.
- Validar antes de permitir publicação `production`.

## Verificação
- teste de serialização round-trip Job→UI→Job;
- teste de resize sem drift;
- teste de clamp para impedir área vazia;
- teste de rotação + cover;
- teste de override individual no Chaveiro.
