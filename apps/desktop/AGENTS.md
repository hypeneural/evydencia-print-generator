# Desktop / Python / Render Rules

- Use pathlib.Path e preserve Unicode/espaços.
- Corrija EXIF Orientation antes de geometria.
- mm→px apenas pela função canônica.
- Render final usa o arquivo original.
- Renderer não depende de Fabric/DOM.
- Output collision-safe; temporário + rename quando possível.
- Nunca sobrescrever input.
- Bridge pywebview pequena e orientada a domínio.
- Paths do Explorer são entrada não confiável.
- Não persistir caminho completo em logs normais.

Use /render-golden-tests para mudanças no bitmap.
