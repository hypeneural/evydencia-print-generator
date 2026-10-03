# Status

**Estado:** Fundação pronta; próximo marco é o vertical slice do Calendário, seguido da integração moderna do Windows 11.

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

## Editor
- Operador e Gestor separados.
- Ingest unificado: context menu, dialog e drag/drop.
- preview proxy desacoplado do original.
- budgets de performance.
- pipeline EXIF/ICC/DPI/JPEG documentado.
- Fabric 7.x + pywebview 6.x + Pillow 12.x como stack atual.

## Windows alvo real
- Windows 11 Home Single Language 25H2 x64.
- i7-11800H / 32 GB RAM / RTX 3060 Laptop 6 GB.
- Produção: IExplorerCommand C++ + sparse MSIX assinado.
- Fallback/dev: classic shell verb per-user.
- Processamento de imagem permanece fora do Explorer.

## Bloqueios físicos
- DPI de produção;
- geometria física do Calendário;
- X/Y do Globo;
- prova física/margens/pareamento do Chaveiro;
- política ICC/profile do laboratório;
- naming final.

## Próximos marcos
1. Issue #4: SourceRegistry + preview + renderer + Calendário.
2. Menu moderno do Windows 11 após o CLI/ingest estarem estáveis.
3. Chaveiro e Globo.
4. Modo Gestor completo.
