---
name: image-ingest-preview
description: "Implementa entrada local de fotos por context menu, file dialog e drag-and-drop, cria previews/proxies deduplicados e mantém o original fora do Fabric. Use em importação de imagem, source registry, cache e bridge pywebview."
---
# Image Ingest & Preview

Leia `docs/IMAGE_PIPELINE.md` e, se necessário, `resources/pywebview-inputs.md`.

## Decision tree
- Veio caminho nativo (CLI/dialog/drop)? → normalize/validate no Python e registre SourceAsset.
- Source já existe por path+size+mtime? → reutilize ID e preview.
- Preview inexistente? → gere assíncrono.
- Original mudou? → invalide preview e metadata.
- App precisa mostrar a foto? → use preview URI, nunca bytes full-res/base64 do original.

## SourceAsset mínimo
- id;
- canonical_path (somente runtime/local; não persistir em logs);
- size_bytes;
- mtime_ns;
- pixel_width/height após EXIF;
- format;
- preview_uri/status;
- ICC presence/metadata mínima.

## Preview
- aplicar EXIF;
- limitar longest side conforme performance budget;
- JPEG de preview pode usar qualidade de tela;
- cache por source fingerprint;
- gerar uma vez e reutilizar em N slots.

## Concurrency
Não iniciar 18 resizes iguais para 18 slots. Deduplicar por source e limitar workers. UI recebe estados queued/loading/ready/error.

## Validação
Teste espaços, Unicode, JPEG grande, PNG, corrupção, source repetida, arquivo alterado e drop múltiplo.
