# EVYDÊNCIA Print Generator — Workspace Contract

Este arquivo é curto por design: fica always-on. Detalhes vivem em AGENTS.md por diretório, Rules condicionais e Skills carregadas sob demanda.

## Missão
Construir um editor desktop Windows profissional e simples para Calendário, Chaveiro e Globo, preservando qualidade de impressão e fluidez operacional.

## Invariantes
1. Um motor, vários templates.
2. Milímetros são a geometria física canônica; pixels derivam do DPI.
3. Fabric usa preview/proxy; o renderer usa o original.
4. Preview não é render final.
5. Template define produto; Job define uma execução.
6. Nunca sobrescrever a foto original.
7. Nunca versionar fotos reais de clientes, familiares ou crianças.
8. V1 é local/offline.
9. Medida desconhecida = draft/TBD; não inventar.
10. Mudança incompatível exige schema version + ADR + testes/migração.
11. Explorer apenas inicia o app; processamento de imagem não roda dentro de explorer.exe.
12. Simplicidade do Operador vence flexibilidade genérica.
13. Geometria física correta não prova UI correta; preview/layout exigem validação visual independente.
14. Teste local verde não prova CI remoto verde; conclusão exige evidência conforme docs/QUALITY_GATES.md.

## Stack aprovada
React + TypeScript + Fabric.js 7.x; Python + pywebview 6.x + Pillow 12.x; JSON Schema; PyInstaller + Inno Setup; C++/IExplorerCommand para o menu moderno do Windows 11.

## Como começar uma tarefa
1. Leia @docs/REPOSITORY_MAP.md.
2. Leia @STATUS.md.
3. Leia apenas os documentos e AGENTS.md da área tocada.
4. Não faça varredura recursiva ou carregue todas as Skills por padrão.

## AntiGravity
- Mudança multi-arquivo, arquitetura, contrato ou risco alto: use /plan e mantenha Request Review.
- Requisito ambíguo: use /grill-me.
- Bug difícil de geometria/performance: /boost quando disponível.
- UI: use /browser para inspeção real após testes determinísticos.
- Correções recorrentes: /learn, revisando o diff antes de persistir Rule/Skill.
- /teamwork-preview só para trabalho realmente repo-scale/long-horizon.
- Subagentes que escrevem em paralelo devem usar escopos/worktrees isolados; nunca dois agentes editando o mesmo arquivo.
- Antes de declarar pronto, aplique docs/QUALITY_GATES.md.

## Áreas
- apps/ui/AGENTS.md
- apps/desktop/AGENTS.md
- native/windows-shell/AGENTS.md
- templates/AGENTS.md
- schemas/AGENTS.md
- installer/AGENTS.md
- tests/AGENTS.md
