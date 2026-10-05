# UI Runtime Architecture

## Três sistemas de coordenadas

### 1. Produção
Vem do Template:
- mm + DPI;
- canvas_px;
- slot_rect_px.

É autoridade do render final.

### 2. Preview/viewport
É derivado do espaço disponível na janela e nunca altera Template/Job.

```text
fitScale = min(
  availableWidth / productionWidth,
  availableHeight / productionHeight,
  1
)

displayWidth  = productionWidth  * fitScale
displayHeight = productionHeight * fitScale
```

Invariante:
`displayWidth / displayHeight == productionWidth / productionHeight`.

Não usar dimensões de produção gigantes no layout DOM e depender somente de `transform: scale(...)` com parent `overflow:hidden`.

A estratégia CSS-only anterior foi substituída por um `viewportTransform` explícito (`[fitScale, 0, 0, fitScale, 0, 0]`) com `setDimensions` no tamanho do viewport (`layout.displayWidth` × `layout.displayHeight`) porque atende melhor aos requisitos de hit-testing nativo (`scenePoint` / `viewportPoint`), menor consumo de memória de backstore e separação clara entre coordenadas de cena e de exibição.

Fontes oficiais Fabric.js:
- https://www.fabricjs.com/api/classes/canvas/#setDimensions
- https://www.fabricjs.com/api/classes/canvas/#setViewportTransform

### 3. Job
Persistir somente:
- source_id;
- pan_x_norm;
- pan_y_norm;
- scale relativo ao cover;
- rotation_deg.

Resize/viewport nunca muda Job.

## Cena Fabric persistente
A cena deve sobreviver ao gesto.

Criar/reconciliar objetos quando:
- template muda;
- source de slot muda;
- slot é criado/removido;
- overlay muda.

Hot path de drag/wheel/slider:
- atualizar o FabricImage existente;
- requestRenderAll coalescido;
- não fabric.clear();
- não FabricImage.fromURL();
- não decodificar preview;
- não reconstruir clipPath a cada frame;
- não setState global React a cada pointermove.

Commit de domínio acontece no fim do gesto.

## Overlay
Calendário:
- overlay ocupa 100% do canvas visual;
- overlay é não-selecionável/não-evented;
- foto fica atrás e é clipada pelo slot;
- scale=1 é cover inicial;
- drag/zoom/rotação alteram somente a foto.

## Startup
Abrir janela primeiro. Preview é assíncrono:
```text
ingest -> window -> loading -> preview ready -> slot updates
```
Não bloquear abertura aguardando thumbnail.

## Interações por produto
- Calendário: double-click/Enter pode focar modo Ajustar.
- Chaveiro: double-click em slot preenchido duplica SlotEditState inteiro para o próximo slot e ativa o destino.
- Globo: double-click em slot preenchido duplica SlotEditState inteiro para o outro slot.
- Sempre manter botão/ação visível equivalente; gesto não deve ser o único caminho acessível.

Fabric.js expõe `mouse:dblclick` oficialmente:
https://www.fabricjs.com/api/interfaces/canvasevents/#mousedblclick

## Validação visual
- Calendário: 1067×1474, retrato.
- Globo: 2551×1205, paisagem (216×102 mm @ 300 DPI).
- Chaveiro: 2551×1795, paisagem.
- switching e resize não alteram proporção nem Job.
