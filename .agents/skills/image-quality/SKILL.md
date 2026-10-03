---
name: image-quality
description: "Preserva qualidade de impressão no pipeline Pillow: EXIF, resize/rotation, ICC, DPI, alpha e codificação JPEG/PNG. Use quando tocar ingest metadata, renderer, export ou configuração de laboratório."
---
# Image Quality

Leia `docs/IMAGE_PIPELINE.md` e `resources/pillow-output-policy.md`.

## Pipeline
1. abrir original;
2. guardar metadata necessária;
3. `ImageOps.exif_transpose`;
4. definir working/output color policy;
5. transformar a partir do original;
6. compor overlay;
7. codificar uma única vez no output final.

## Resampling
- LANCZOS para redução/resize final quando aplicável.
- Transformações afins/rotação usam o melhor filtro suportado e precisam golden test.
- Evitar cadeias de resize repetidas.

## JPEG
A política de projeto é quality=95 como teto padrão de qualidade útil; não usar 100 automaticamente. Definir subsampling de produção explicitamente quando aprovado pelo laboratório.

## ICC
Não remover profile silenciosamente. Com múltiplas fontes, o output precisa de um único profile/working space definido; até confirmação do laboratório, tratar política como decisão pendente e testável.

## DPI
Gravar `dpi=(template_dpi, template_dpi)` e verificar dimensão em pixels.

## Verificação
Golden PNG para geometria; testes específicos para JPEG, DPI e ICC; comparação visual/tolerância, não hash JPEG cross-platform.
