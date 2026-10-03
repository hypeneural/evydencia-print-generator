---
name: editor-ux
description: "Projeta e revisa a UX profissional e simples dos modos Operador e Gestor: seleção de slots, crop/zoom/rotação, source tray, layers, history, feedback e prevenção de erros. Use antes ou durante mudanças visuais do editor."
---
# Editor UX

Leia `docs/EDITOR_UX.md`. Não desenhe um Canva genérico.

## Decision tree
- Ação necessária em todo ensaio? → Operador, visível sem menu avançado.
- Ação altera estrutura do produto/template? → Gestor.
- Ação pode destruir trabalho? → undo/redo obrigatório e confirmação somente se não for reversível.
- Campo técnico só serve ao sistema? → ocultar; mostrar linguagem de produção.
- Recurso raro/avançado? → inspector/context menu, não toolbar primária.

## Operador — superfície mínima
- bandeja de fotos;
- canvas;
- slot selecionado com borda clara;
- trocar foto;
- zoom;
- girar/alinhar;
- reset;
- duplicar/aplicar ao par quando houver;
- undo/redo;
- gerar.

### Gestos
- click: selecionar slot;
- drag dentro do slot: mover foto;
- wheel sobre slot ativo: zoom;
- double click ou Enter: Ajustar;
- Escape: sair de Ajustar;
- Ctrl+Z / Ctrl+Y: history.

## Gestor
Adicionar:
- criar/mover/redimensionar slot;
- snap/guias;
- layer list;
- trazer para frente/enviar para trás;
- lock/visibility;
- group;
- overlay/assets;
- medidas em mm;
- publish/version.

## Regra de layers
No Operador, "para frente/trás" não pode quebrar o produto. A foto permanece dentro da layer do slot. Reordenação estrutural é Gestor.

## Teste de UX
Para cada mudança valide happy path, empty/loading/error, mouse, keyboard, undo e comportamento em 1366x768 e 1920x1080.
