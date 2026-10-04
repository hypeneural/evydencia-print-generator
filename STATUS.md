# Status

**Estado:** M1 (Calendário) 100% concluído e validado em produção local. Próximos marcos: integração com o menu de contexto do Windows 11 (Fase 3 / Issue #5) e expansão para Chaveiro e Globo.

## Infra concluída
- AntiGravity 2.19.1 auditado contra documentação oficial.
- `evydencia-builder` + especialistas de produto, UX, Fabric, render, Windows e QA.
- Rules/Skills/Hooks com validação mecânica.
- Repository Map para reduzir exploração desnecessária.
- Schemas Template/Job v1.
- Templates draft: Chaveiro, Calendário, Globo.
- Python package mínimo + mm→px.
- CI Linux + Windows verde.
- PR/Issue templates adicionados.

## M1 — Calendário Concluído
- E1: SourceRegistry + Ingest único para CLI/dialog/drop com fingerprint V1.
- E2: Preview pipeline com decode proporcional (draft), cache LRU e retenção.
- E3: Renderer determinístico via Pillow (transformada afim ADR-011, overlay RGBA, ICC, DPI e proteção contra sobrescrita).
- E4: Editor do Operador em React 19 + Fabric 7.4.0 + pywebview com bridge assíncrono e servidor de assets efêmero.
- E5: Paridade de crop 100% comprovada (0px de divergência), baseline de performance documentado (`docs/benchmarks/M1_BASELINE.md`), validação real em fotos de 24 MP com render em ~290ms.

## Windows alvo real
- Windows 11 Home Single Language 25H2 x64.
- i7-11800H / 32 GB RAM / RTX 3060 Laptop 6 GB.
- Produção: IExplorerCommand C++ + sparse MSIX assinado.
- Fallback/dev: classic shell verb per-user.
- Processamento de imagem permanece fora do Explorer.

## Bloqueios físicos resolvidos / pendentes
- [x] Calendário: geometria e overlay PNG validados com `moldura.png` real.
- [ ] DPI de produção final para impressão química/térmica em laboratório.
- [ ] Chaveiro: pareamento e margens de corte em prova física.
- [ ] Globo: simetria lado a lado e proporção sem PNG transparente.

## Próximos marcos
1. Issue #5: Integração com menu de contexto moderno do Windows 11 (`IExplorerCommand`).
2. M2: Chaveiro (18 slots, duplex, pareamento).
3. M3: Globo de Neve (2 slots simétricos, proporções 5x8cm).
4. Modo Gestor completo.
