# UI / Fabric.js Rules

- A UI edita Job state; não é fonte da geometria física nem do bitmap final.
- Fabric.js é runtime, não contrato persistente. Nunca usar JSON bruto Fabric como Template/Job público.
- Geometria física vem do Template em mm.
- Persistir transformações normalizadas independentes da viewport.
- cover_required=true impede área vazia.
- Overlay fica bloqueado no modo Operador.
- Operador: substituir, arrastar, zoom, rotação, reset e gerar.
- Não exportar produção do browser; frontend envia Template + Job ao renderer Python.
- Resize da janela não altera resultado lógico.
- Não adicionar ferramentas genéricas sem requisito.

Use /fabric-canvas ao mudar clipping/transform/serialização.
