# UI / Fabric.js Rules

## Papel da UI
A UI projeta Template + Job para interação. Ela não define a verdade física e não exporta o bitmap final de produção.

## Performance e memória
- Nunca carregar o JPEG original de câmera no Fabric no fluxo normal.
- Usar apenas previews/proxies gerados/deduplicados pelo ingest pipeline.
- Uma mesma source deve reutilizar o mesmo preview decodificado sempre que possível.
- Evitar zoom contínuo do viewport; o zoom principal é da foto dentro do slot.
- Coalescer eventos de drag/wheel/slider por animation frame e criar uma única entrada de histórico ao fim da interação.
- Construções em lote devem evitar render a cada objeto; renderizar uma vez após o batch.
- Medir antes de alterar configurações globais de cache do Fabric.

## Estado
- Template/Job são a fonte persistente.
- Nunca salvar JSON bruto do Fabric como contrato público.
- Transformações persistidas são normalizadas e independentes do tamanho da janela.
- History/undo-redo opera sobre comandos de domínio, não sobre pixels/snapshots grandes.

## Operador
Expor somente:
- adicionar/substituir foto;
- clicar slot;
- arrastar foto dentro do slot;
- zoom;
- rotação/alinhar;
- reset;
- duplicar/aplicar a par quando o produto permitir;
- undo/redo;
- gerar.

Não expor painel genérico de layers, coordenadas, DPI ou propriedades Fabric.

## Gestor
Pode editar:
- canvas físico;
- slots;
- groups;
- overlays/assets;
- ordem/lock/visibilidade de layers;
- permissões;
- naming/output;
- publish/version.

Objetos de sistema/overlay protegido permanecem bloqueados até ação explícita.

Use /editor-ux, /fabric-canvas e /editor-performance.
