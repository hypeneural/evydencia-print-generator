---
name: print-geometry
description: Calcula e verifica geometria física de impressão, conversão mm↔px, margens, grids, DPI e arredondamento. Use ao definir dimensões, posicionar slots ou investigar divergência de tamanho.
---
# Print Geometry

## Regra canônica
`px = round(mm / 25.4 * dpi)`

- Um único helper deve implementar essa regra no runtime.
- Nunca converter de px de screenshot para mm quando a medida física real estiver pendente.
- Para grids, valide `margens + slots + gaps = canvas` por eixo.
- Registre qualquer derivação geométrica como `derived`, não como medição física observada.
- Para `production`, todas as coordenadas devem estar resolvidas e dentro do canvas.

## Chaveiro conhecido
- canvas 216×152 mm
- slot 34×44 mm
- grid 6×3
- grid ocupa 204×132 mm
- centralização matemática deriva 6 mm laterais e 10 mm verticais; esta centralização ainda precisa de validação física antes de `production`.

Use `.agents/skills/print-geometry/scripts/mm_to_px.py` para conferências rápidas.
