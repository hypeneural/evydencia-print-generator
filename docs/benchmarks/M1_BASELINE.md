# M1 — Baseline de Performance (Final Consolidado)

Máquina: Perfil em `docs/DEV_MACHINE_PROFILE.md`
- Intel Core i7-11800H @ 2.30 GHz (8c/16t)
- 32 GB RAM DDR4 3200 MT/s
- NVIDIA GeForce RTX 3060 Laptop GPU 6 GB
- Windows 11 Home Single Language 25H2 x64
- Python 3.13.1, Pillow 12.3.0, Node.js 22.14.0, React 19, Fabric.js 7.4.0

---

## 1. Amostra Real de Teste (Fotografias de Cliente)
- 5 fotos reais de cliente, **estritamente locais, nunca versionadas no git** (`Foto_teste`).
- Câmera Canon EOS R6 Mark II, 6000 × 4000 px (24 MP), 7,2–9,4 MB.
- Container **MPO** (JPEG primário + MPF secundário). Sem ICC embutido; EXIF ColorSpace = sRGB.
- Moldura de produção: `moldura.png` (1067 × 1474 px, RGBA, slot vazado 823 × 395 px).

---

## 2. Resultados Consolidados vs Performance Budgets

| Operação | Target / Budget | Medido no Windows 11 (p50 / p95) | Status |
|---|---:|---:|:---:|
| **Ingest (E1)** (header probe + verify + EXIF) | < 100 ms | **19,7 ms – 22,6 ms** | ✅ APROVADO |
| **Preview Cold (E2)** (24 MP -> 2048 px proxy q85) | <= 1.000 ms | **269 ms – 304 ms** | ✅ APROVADO |
| **Preview Cache Hit** (lookup no disco local) | < 150 ms | **0,18 ms** | ✅ APROVADO |
| **Render Produção (E3)** (24 MP + affine + overlay RGBA + q95) | <= 2.000 ms | **289 ms – 385 ms** | ✅ APROVADO |
| **Editor Drag / Zoom (E4)** (Fabric 7.x 60 FPS target) | >= 30 FPS | **60 FPS estável** | ✅ APROVADO |
| **Crop Parity (UI vs Pillow)** | < 1 px divergence | **0 px (erro < 1e-5)** | ✅ APROVADO |
| **Integridade de Arquivo Original** | Imutável | **mtime e tamanho 100% preservados** | ✅ APROVADO |

---

## 3. Detalhamento Técnico das Etapas

### Ingest (E1)
- Identidade V1: `normalized_path + size + mtime_ns` com fingerprint SHA-256 (32 chars) sem hashing integral de JPEG pesado.
- Probe seguro em streaming lê dimensões reais, orientação EXIF e mapeia contêiner MPO Canon sem decodificar imagem completa.

### Preview Pipeline (E2)
- **Otimização Crítica:** `Image.draft("RGB", (2048, round(orig_h * scale)))` com cálculo proporcional aciona o decodificador DCT 1/2 na biblioteca libjpeg-turbo do Pillow.
- Tempo de decode cai de ~870 ms para ~300 ms por imagem de 24 MP.
- Cache determinístico local com retenção por tamanho e idade (`PreviewCache`).

### Renderer Determinístico (E3)
- Renderização via transformada afim inversa ADR-011 (`slot_to_source_affine`).
- Reabre o original de 24 MP com preservação de perfil ICC e DPI explícito.
- Overlay RGBA de alta fidelidade via `alpha_composite`.
- Política de colisão de saída: resolve nomes não-destrutivos (`Calendario_<stem>_002.jpg`) com proteção cross-platform case-insensitive.

### Editor do Operador (E4)
- React 19 + TypeScript 6 + Fabric 7.4.0.
- Canvas restrito ao operador: overlay travado (`selectable: false, evented: false`), slot clipPath ativo, controles de pan, zoom e rotação (90° steps).
- Histórico de comandos com Undo / Redo limpo (sem serialização contínua de canvas).
- Servidor HTTP efêmero (`AssetServer`) servindo previews e assets locais com cabeçalho `Connection: close` para evitar travamento de sockets.
- Bridge pywebview (`DesktopBridge`) conectando a interface ao backend Python.

### Paridade e Hardening (E5)
- Script de teste de produção ponta a ponta: `scripts/test_production_e2e.py`.
- Suíte automatizada de paridade: `tests/test_parity.py` com prova matemática de invariância de escala (preview vs full-res).
- 108 testes passando com 0 erros de linting no Ruff e conformidade 100% de privacidade (`scripts/check_privacy.py`).
