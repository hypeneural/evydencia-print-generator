# Upstream References

A regra é **extrair padrões, não acoplar o produto a um editor genérico**.

## Adopt

### Fabric.js
https://github.com/fabricjs/fabric.js

Papel: canvas/interação. Versão-alvo atual 7.4.0.

### pywebview
https://github.com/r0x0r/pywebview

Papel: janela desktop e bridge Python↔JS, file dialog e drag/drop.

### Pillow
https://github.com/python-pillow/Pillow

Papel: renderer final de alta resolução.

### JSON Schema
https://json-schema.org/

Papel: contratos Template/Job.

## Architecture references — editor

### bensitu/image-editor
https://github.com/bensitu/image-editor

Fabric.js v7, TypeScript, modular, MIT.

Extrair ideias de:
- core lifecycle separado;
- plugins tipados;
- operações transacionais;
- history com recording control;
- objetos de sessão não persistidos;
- snapshots seguros;
- migration separada.

Não adotar export/feature set inteiro.

### ascentspark/react-image-editor
https://github.com/ascentspark/react-image-editor

React 19 + Fabric.js v7.

Extrair ideias de:
- integração React/Fabric moderna;
- crop/rotate/layers;
- theming/API boundaries.

### salgum1114/react-design-editor
https://github.com/salgum1114/react-design-editor

Extrair UX de:
- guides/snap;
- layer list;
- crop;
- drag/drop;
- undo/redo.

É referência de UX, não base arquitetural principal.

## Architecture references — Windows

### Microsoft packaged File Explorer integration
https://learn.microsoft.com/windows/apps/desktop/modernize/integrate-packaged-app-with-file-explorer

Fonte primária para IExplorerCommand + sparse MSIX.

### Microsoft ExplorerCommandVerb sample
https://github.com/microsoft/Windows-AppConsult-Samples-DesktopBridge

Referência de implementação COM/selection/Invoke.

### Microsoft PowerToys
https://github.com/microsoft/PowerToys

Referência de produção para:
- modern vs classic handler;
- sparse MSIX;
- signing;
- filtering;
- update/uninstall lifecycle;
- per-user installation.

## Alternatives a benchmarkar, não adotar agora

### libvips/pyvips
Considerar somente se benchmarks reais mostrarem Pillow insuficiente para preview/render. Adiciona dependência nativa e complexidade de packaging.

## Policy

Uma dependência/referência nova precisa responder:
1. qual problema específico resolve;
2. por que o stack atual não resolve;
3. licença;
4. manutenção;
5. impacto no bundle/installer;
6. como sair dela no futuro.
