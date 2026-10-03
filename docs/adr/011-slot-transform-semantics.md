# ADR-011 — Semântica do transform por slot

**Status:** Aceito (M1, Issue #4)

## Contexto
`job.schema.json` v1.0 define `pan_x_norm`, `pan_y_norm`, `scale` e `rotation_deg`, mas não define faixa, sinal, referencial nem a interação entre rotação e cover. Sem essa definição, Fabric (preview) e Pillow (render) divergem. Esta ADR fixa a semântica **sem mudar a estrutura do schema** (compatível com v1.0).

## Decisão

### Referenciais
- Slot em pixels: retângulo `W×H` derivado de mm + DPI pelo helper canônico.
  Bordas são convertidas independentemente: `left = mm_to_px(x_mm)`, `right = mm_to_px(x_mm + width_mm)`, `W = right - left` (idem em y). Isso evita gaps/overlaps acumulados em grids.
- Source: imagem **após EXIF orientation**, `w×h` px.
- Coordenadas contínuas com origem no canto superior esquerdo e eixo y para baixo; pixel `i` cobre `[i, i+1)`.

### rotation_deg
- Positivo = **horário na tela** (mesma convenção do `angle` do Fabric).
- Normalizado no domínio para `[-180, 180)`. Múltiplos exatos de 90° usam seno/cosseno exatos.

### Cover dependente da rotação
Bounding box do slot no referencial da foto:

```
W' = W·|cos θ| + H·|sin θ|
H' = W·|sin θ| + H·|cos θ|
s_cover(θ) = max(W'/w, H'/h)
```

### scale
- Relativo ao cover **na rotação atual**: `s_eff = scale · s_cover(θ)` (source px → slot px).
- Faixa `[1, SCALE_MAX]`, `SCALE_MAX = 8` (constante da aplicação, não do schema).
- `scale = 1` nunca revela área vazia, em qualquer rotação. Consequência de UX: girar aplica zoom automático mínimo.

### pan_x_norm / pan_y_norm
- Faixa `[-1, 1]`, medidos **nos eixos da foto rotacionada**, em unidades do slot:

```
max_dx = max(0, (w·s_eff − W') / 2)
max_dy = max(0, (h·s_eff − H') / 2)
offset = (pan_x_norm · max_dx, pan_y_norm · max_dy)
```

- `0` = centralizado; `±1` = limite antes de revelar vazio; positivo desloca o conteúdo para +x/+y da foto.
- O centro da foto no slot é `centro_do_slot + R(θ)·offset`, onde `R(θ)` é a rotação horária em coordenadas y-para-baixo.
- O limite usa a bbox do slot: é exato em 0/90/180/270° e conservador em ângulos oblíquos (pan um pouco menor), em troca de zero cantos vazios e fórmula fechada idêntica em Python e TypeScript.

### Clamp
Clamp e normalização acontecem no domínio (`domain/transform.py` e o espelho em TS), nunca no runtime Fabric. Valores não finitos são rejeitados.

### Mapeamento para o render
O renderer usa a afim inversa slot→source derivada desta ADR (`slot_to_source_affine`). O preview Fabric usa a mesma placement (centro, `s_eff`, θ) escalada pela razão preview/original e pela escala de exibição.

## Consequências
- `tests/fixtures/transform_vectors.json` é a fonte de paridade Python↔TypeScript.
- Mudar qualquer fórmula acima exige nova ADR + regenerar vetores + golden tests.
- Zoom e rotação preservam o pan normalizado (posição relativa), sempre reaplicando o clamp.
- `allow_pan/allow_zoom/allow_rotate = false` exigem respectivamente pan 0, scale 1 e rotação 0 no Job.
