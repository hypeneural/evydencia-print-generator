# UI / Fabric.js Rules

## Papel
A UI projeta Template + Job para interação. Não define geometria física nem export final.

Leia também:
- docs/UI_RUNTIME_ARCHITECTURE.md
- docs/EDITOR_UX.md
- docs/PERFORMANCE_BUDGETS.md

## Coordenadas
- Template/produção, PreviewLayout e Job são sistemas distintos.
- Resize altera somente PreviewLayout.
- Nunca persistir left/top/scaleX/angle bruto do Fabric.
- Aspect ratio visual deve ser igual ao canvas de produção.

## Runtime Fabric
- Cena persistente: não limpar/recriar toda a cena por mudança de pan/zoom.
- Nenhum `fabric.clear()`, `FabricImage.fromURL()` ou decode no hot path de pointermove/wheel.
- Reutilizar FabricImage, clipPath, overlay e preview por source.
- Atualização de alta frequência por refs/requestAnimationFrame.
- React/domain state recebe commit no fim do gesto.
- Um gesto contínuo = uma entrada no history.

## Imagem
- Nunca carregar original full-resolution no Fabric.
- Preview/proxy é deduplicado.
- scale=1 significa cover mínimo.
- overlay protegido é non-selectable/non-evented.

## Operador
Somente intenção operacional: adicionar/trocar, selecionar slot, mover foto, zoom, rotação, reset, ações do produto, undo/redo, gerar.

## Gestor (M5)
- Shared Editor Runtime: reutiliza `ProductCanvas.tsx` alternando capabilities pelo prop `mode="manager"`.
- Nunca duplicar o canvas criando `ManagerCanvas.tsx`.
- Manipulação de slots no Gestor opera em milímetros (`draft.ts`), refletida em `rect_px` por `mm_to_px(mm, dpi)`.
- Edição opera sobre `TemplateDraft` efêmero; publicação em disco é atômica e versionada.

## Validação
Mudança visual precisa de evidência visual; testes de renderer não substituem UI.
Use /ui-visual-validation, /fabric-canvas e /editor-performance.
