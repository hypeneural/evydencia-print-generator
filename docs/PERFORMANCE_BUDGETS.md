# Performance Budgets

Targets de engenharia; medir antes/depois.

## Máquina de referência
Ver docs/DEV_MACHINE_PROFILE.md.

## Targets
| Operação | Target inicial |
|---|---:|
| janela utilizável após launch | <= 2.5 s cold |
| source aceita -> preview ready | p95 <= 1.0 s |
| click/toolbar feedback | < 100 ms |
| hot frame de drag/zoom | ideal <= 16.7 ms; não sustentar < 30 fps |
| undo/redo | perceptivelmente imediato |
| source em cache -> slot | < 150 ms visual |
| UI durante render | sem freeze |

## Hot path proibido
Durante pointermove/wheel/slider contínuo:
- não decodificar imagem;
- não FabricImage.fromURL();
- não fabric.clear();
- não reconstruir a cena inteira;
- não criar preview por slot;
- não persistir pixels;
- não fazer setState global React a cada frame.

Use estado efêmero próximo ao canvas, refs e requestAnimationFrame/coalescing. Commit no domínio/history ao final do gesto.

## Viewport
- geometria de produção e geometria de exibição são separadas;
- resize recalcula somente PreviewLayout;
- aspect ratio deve permanecer exato;
- não usar canvas de produção gigante + CSS scale como única estratégia de fit.

## Startup
Preview é assíncrono. Não atrasar a criação da janela esperando thumbnails.

## Fabric cache
Object caching possui tradeoffs de memória/qualidade. Alterar objectCaching/noScaleCache/limites globais somente com profile antes/depois.

Fonte:
https://www.fabricjs.com/docs/fabric-object-caching/

## Evidência
Registrar:
- CPU/RAM/GPU e display scale/DPR;
- janela;
- quantidade de sources/slots;
- cold/warm cache;
- p50/p95;
- memória;
- Performance recording/flamegraph quando houver jank.

Mudança que piora interação/source load precisa justificar custo antes do merge.
