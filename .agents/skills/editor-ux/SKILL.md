---
name: editor-ux
description: "Projeta e revisa UX do Operador/Gestor: slots, crop, zoom, rotação, duplicação por produto, feedback, acessibilidade e prevenção de erro. Use em mudanças de interação."
---
# Editor UX

Leia docs/EDITOR_UX.md e docs/UI_RUNTIME_ARCHITECTURE.md.

## Decision tree
- uso recorrente? -> Operador;
- altera estrutura/template? -> Gestor;
- gesto essencial? -> fornecer alternativa visível;
- ação destrutiva? -> undo/redo e confirmação só se irreversível;
- termo técnico interno? -> ocultar do Operador.

## Gestos comuns
- click: selecionar slot;
- drag: mover foto;
- wheel: zoom;
- Escape: sair de ajuste;
- Ctrl+Z/Ctrl+Y: history.

## Double-click por produto
- Calendário: focar/alternar Ajustar.
- Chaveiro: clonar SlotEditState inteiro para o próximo slot e ativá-lo.
- Globo: clonar SlotEditState inteiro para o outro slot.
- Uma clonagem = uma entrada no history.
- O gesto nunca é a única forma de executar uma ação essencial.

## Visual
Preview deve preservar aspect ratio de produção e continuar correto em switching/resize.

## Teste
Happy path + empty/loading/error + teclado + undo + 1024×680/1280×800/1920×1080.
