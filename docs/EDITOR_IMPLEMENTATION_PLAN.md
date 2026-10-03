# Editor Implementation Plan — Vertical Slice

## Estratégia
Não construir o modo Gestor inteiro antes de provar o núcleo. O próximo passo é um vertical slice completo do **Calendário** usando foto real local somente no ambiente do estúdio, com fixtures sintéticas nos testes.

## E1 — SourceRegistry + ingest
Entregar:
- entrada CLI;
- file dialog multi-select;
- drag/drop pywebview;
- validação;
- SourceAsset;
- preview cache 2048px;
- dedupe e estados loading/error.

Gate:
- a mesma foto em dois slots/source usages cria um preview;
- UI nunca recebe original base64/full-res.

## E2 — Renderer core antes da paridade visual
Entregar:
- EXIF transpose;
- cover;
- pan;
- zoom;
- rotate;
- clip;
- overlay;
- JPEG/PNG output;
- DPI;
- atomic/collision-safe save;
- golden tests.

Gate:
- transform fixtures calculáveis e golden aprovados.

## E3 — Calendar operator editor
Entregar:
- Vite/React shell;
- canvas Fabric;
- um slot sob overlay;
- click/drag/wheel/rotate/reset;
- Job state;
- undo/redo;
- Gerar chama renderer.

Gate:
- resize da janela não muda Job;
- preview e output têm crop visualmente equivalente;
- performance budget medido.

## E4 — Chaveiro
- 18 slots;
- source tray;
- quantidade;
- fill quantity/fill sheet;
- override individual;
- pair behavior somente após confirmação física.

## E5 — Globo
- dois slots;
- source independente;
- duplicate source;
- ajuste independente.

## E6 — Manager mode + Template schema 1.1
Somente depois dos três produtos:
- layers genéricas referenciando slot/asset/background;
- z-order;
- lock/visibility;
- guides/snap;
- create/duplicate/delete slot;
- publish/version.

Antes de alterar schema v1.0: ADR + migration + tests.

## E7 — Windows distribution
- PyInstaller;
- Inno Setup;
- classic context menu;
- open direct;
- install/uninstall matrix;
- multi-select opcional depois.

## Definição de "editor profissional simples"
- zero JSON manual;
- zero DPI/pixel para Operador;
- qualquer ajuste reversível;
- source add por botão e drag/drop;
- slot selecionável em um clique;
- crop via arrastar/zoom;
- feedback imediato;
- output de alta qualidade produzido do original.
