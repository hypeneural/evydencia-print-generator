# ADR-003 — Fabric.js no preview, Pillow no render

**Status:** Aceito

## Decisão
Fabric.js cuida da interação visual. Pillow refaz a composição final sobre arquivos originais.

## Consequências
- JSON interno do Fabric não é contrato persistente;
- Job guarda transforms normalizados;
- resize da UI não muda output;
- golden tests pertencem ao renderer.
