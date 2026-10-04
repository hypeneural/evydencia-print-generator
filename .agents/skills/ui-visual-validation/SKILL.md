---
name: ui-visual-validation
description: "Valida visualmente viewport, aspect ratio, overlay, switching, resize e gestos do editor. Use quando UI pode estar tecnicamente verde mas visualmente incorreta."
---
# UI Visual Validation

## Princípio
Output/render correto não prova preview correto.

## Decision tree
- mudança só de domínio sem UI? -> skill não necessária;
- layout/aspect/overlay/interaction mudou? -> validação visual obrigatória;
- existe Vite/bridge mock? -> valide no browser;
- não existe E2E visual? -> use /browser com fixture sintética e documente gap; proponha teste automatizado em /plan.

## Matriz mínima
- 1024×680;
- 1280×800;
- 1920×1080;
- Calendário -> Globo -> Chaveiro -> Calendário;
- resize em cada produto.

## Invariantes
- Calendário 1067/1474 retrato;
- Globo 1795/1205 paisagem;
- Chaveiro 2551/1795 paisagem;
- overlay Calendário cobre canvas inteiro;
- foto inicia em cover;
- resize não altera Job;
- switching não herda dimensões CSS erradas.

## Interação
Validar drag, wheel, reset, undo/redo e double-click específico do produto.

## Evidência
Screenshot/recording somente com fixture sintética. Reporte VISUAL PASS separado de unit/renderer PASS.
