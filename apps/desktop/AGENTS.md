# Desktop / Python / Render Rules

## Ingest
- Entradas podem vir de CLI/context menu, file dialog ou drag/drop pywebview.
- Normalize com pathlib.Path e preserve Unicode/espaços.
- Valide assinatura/formato real, não apenas extensão.
- Registre source por ID lógico; dedupe por path normalizado + size + mtime antes de considerar hash.
- Gere preview assíncrono e cacheável; não envie original/base64 gigante ao JS.

## Preview
- Aplique EXIF Orientation no preview.
- Preview é descartável e pode ser JPEG de tela; nunca vira output final.
- Cache deve viver em diretório local temporário/app-data e possuir política de limpeza.

## Render
- Sempre reabra o original.
- Corrija EXIF antes da geometria.
- Use helper canônico mm→px.
- Reaplique cover/pan/zoom/rotação a partir do Job.
- Preserve/normalize color profile conforme política documentada; nunca remova ICC silenciosamente.
- Output collision-safe e preferencialmente temp + atomic replace/rename.
- Nunca sobrescrever input.

## Bridge
- pywebview expõe uma API de domínio pequena: ingest, list sources, load template, render, choose files, reveal output.
- Não expor filesystem arbitrário ao JavaScript.
- Chamadas longas não podem congelar a UI; retornar job/progress state.

Use /image-ingest-preview, /image-quality e /render-golden-tests.
