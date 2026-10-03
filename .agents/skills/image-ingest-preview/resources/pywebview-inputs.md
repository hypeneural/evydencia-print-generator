# pywebview image input references

Official docs validated 2026-10-03:

- File dialog supports `allow_multiple=True`.
  https://pywebview.flowrl.com/api/
- Python-side DOM `drop` events expose full native file path via `pywebviewFullPath`.
  https://pywebview.flowrl.com/examples/drag_drop
- High-frequency DOM events support debounce through `DOMEventHandler`.
  https://pywebview.flowrl.com/guide/dom

Project rule: all entry methods call the same Python ingest service; JavaScript never invents filesystem paths.
