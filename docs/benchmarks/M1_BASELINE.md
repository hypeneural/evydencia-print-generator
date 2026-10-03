# M1 — Baseline de performance (em construção)

Máquina: perfil em `docs/DEV_MACHINE_PROFILE.md` (i7-11800H, 32 GB, Windows 11 Home 25H2). Python 3.13.1, Pillow 12.3.0.

## Amostra real (2026-10-03)
- 5 fotos reais de cliente, **somente locais, nunca versionadas**.
- Câmera Canon EOS R6 Mark II, 6000 × 4000 px (24 MP), 7,2–9,4 MB.
- Container **MPO** (JPEG primário + imagem secundária MPF). Sem ICC embutido; EXIF ColorSpace = sRGB (Interop R98).
- 1 de 5 com EXIF Orientation 8 (retrato).
- Subsampling 4:2:0; JFIF/EXIF dpi 350 (irrelevante: o output usa o DPI do template).

## Ingest (E1)
| Cenário | Resultado |
|---|---|
| 5 fotos reais (header probe + verify) | 113 ms total |
| 9 artes reais via CLI (inclui partida do Python) | 610 ms total |

## Preview 2048 px (protótipo para E2, ainda não é o código do PR B)
| Pipeline | p50 | max |
|---|---:|---:|
| `draft((2048,2048))` + transpose + LANCZOS + JPEG q85 | 870 ms | 901 ms |
| `draft(<tamanho alvo proporcional>)` + transpose + LANCZOS + JPEG q85 | **304 ms** | 313 ms |
| referência: decode completo 24 MP + transpose | 331 ms | 378 ms |

**Lição:** `Image.draft()` só reduz se *ambas* as dimensões do pedido couberem no fator DCT. Pedir `(2048, 2048)` em 6000 × 4000 não reduz nada (4000/2 < 2048). É preciso pedir o tamanho-alvo proporcional (`2048 × 1365`), o que permite decode em 1/2 (3000 × 2000). PR B deve testar que o draft realmente reduz.

## Observação de produto
A janela da moldura do Calendário tem proporção ≈ 2,09 : 1. Uma foto 3:2 paisagem mantém ~72 % da altura no cover; uma foto retrato 2:3 mantém só ~32 % da altura. Pan/zoom no editor é essencial para retratos.

## Pendente
- render final (E3), janela cold start, FPS de drag/zoom, memória (E4/PR E).
