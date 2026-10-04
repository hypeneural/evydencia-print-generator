# Status

**Estado:** M1 (Calendário) e M2 (Globo de Neve & Chaveiro 3x4) 100% concluídos e validados em produção real. Próximo marco: Integração do Menu de Contexto do Windows 11 (Issue #5).

## Infra concluída
- AntiGravity 2.19.1 auditado contra documentação oficial.
- `evydencia-builder` + especialistas de produto, UX, Fabric, render, Windows e QA.
- Rules/Skills/Hooks com validação mecânica.
- Repository Map para reduzir exploração desnecessária.
- Schemas Template/Job v1.
- Templates produção: Chaveiro (18 slots, 300 DPI), Globo (2 slots, 300 DPI); Template draft: Calendário.
- Python package mínimo + mm→px.
- CI Linux + Windows verde.
- PR/Issue templates adicionados.

## M1 — Calendário Concluído
- E1: SourceRegistry + Ingest único para CLI/dialog/drop com fingerprint V1.
- E2: Preview pipeline com decode proporcional (draft), cache LRU e retenção.
- E3: Renderer determinístico via Pillow (transformada afim ADR-011, overlay RGBA, ICC, DPI e proteção contra sobrescrita).
- E4: Editor do Operador em React 19 + Fabric 7.4.0 + pywebview com bridge assíncrono e servidor de assets efêmero.
- E5: Paridade de crop 100% comprovada (0px de divergência), baseline de performance documentado (`docs/benchmarks/M1_BASELINE.md`), validação real em fotos de 24 MP com render em ~290ms.

## M2 — Multi-Produto (Globo de Neve & Chaveiro 3x4) Concluído
- Globo de Neve: 2 slots de 50x80 mm centralizados em folha 152x102 mm (10x15 cm) com gap de 7 mm e marcas de corte de 1px (render em ~450ms).
- Chaveiro 3x4: 18 slots de 34x44 mm em folha 216x152 mm (15x21 cm paisagem) com grade 6x3 e marcas de corte para guilhotina (render otimizado em ~940ms com cache de decode).
- Editor Operador: Seletor de produtos, seleção visual de slot ativo no canvas Fabric.js, destaque em azul, ações em lote ("Usar mesma foto nos dois", "Preencher todos os 18 slots").
- Suíte de testes automatizada `tests/test_multi_product.py` e validação E2E `scripts/test_production_e2e.py --template all`.

## Windows alvo real
- Windows 11 Home Single Language 25H2 x64.
- i7-11800H / 32 GB RAM / RTX 3060 Laptop 6 GB.
- Produção: IExplorerCommand C++ + sparse MSIX assinado.
- Fallback/dev: classic shell verb per-user.
- Processamento de imagem permanece fora do Explorer.

## Bloqueios físicos resolvidos
- [x] Calendário: geometria e overlay PNG validados com `moldura.png` real.
- [x] Globo: 2 slots simétricos 50x80mm em papel 10x15cm com linhas de corte de 1px a 300 DPI.
- [x] Chaveiro: 18 slots 34x44mm em folha 15x21cm com grade 6x3 a 300 DPI.

## Próximos marcos
1. Issue #5: Integração com menu de contexto moderno do Windows 11 (`IExplorerCommand` + sparse MSIX).
2. Modo Gestor completo.
