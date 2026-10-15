# Chaveiro 3x4 — auditoria de UX e roteiro Windows 11 Home
**Escopo estrito: interação visual do operador.** Branch `codex/keychain-multiselect-dblclick-ux-20261015`; base `e1a411b3802e55038b706f64a4b806d8189df7d5` (PR #27).

## Causa-raiz comprovada no código original
- `ProductCanvas.tsx` recebe Fabric `mouse:down` **antes** de `mouse:dblclick`. Um clique sem Shift em membro não ativo de um grupo selecionado disparava `handleSelectSlot`, colapsando `selectedSlotIds` antes do evento de duplicação.
- `App.tsx:handleDoubleClickSlot` chamava sempre `duplicateSlot` (somente um item), sem reaproveitar `duplicateSelectedSlots` já implementada na ação da barra.
- Bordas secundárias ciano eram mutações do `slotBordersRef` criados sob as fotografias no Fabric; o carregamento assíncrono das imagens colocava fotografias acima dessas bordas. Seletor visual por trás não oferece feedback confiável.

## Alteração cirúrgica (NÃO muda a arte)
- `domain/keychain_selection.ts` define o comportamento determinístico: clique em membro do grupo preserva o conjunto e muda apenas o foco ativo; Shift+clique adiciona/remove; clique fora começa seleção única.
- `App.tsx`: ref sincronizada para seleção atual durante sequência de eventos; duplo clique em qualquer foto pertencente a grupo de tamanho >1 usa **a mesma** função `duplicateSelectedSlots` que o botão; uma ação resulta em **um** commit de histórico/undo. Sem foto selecionada, não duplica. Produtos Globo e Calendário seguem lógica anterior.
- `ProductCanvas.tsx`: **somente no modo Operador do chaveiro** desenha retângulos HTML `pointerEvents: none` com tracejado vermelho (todos os selecionados exceto ativo) **acima** das imagens Fabric. O ativo mantém o tracejado azul existente. Retângulos vermelho têm inset em pixels de tela para não ocultar o azul dos slots vizinhos. Nunca entram na composição Python ou JPEG.
- Barra de seleção: membros não ativos aparecem vermelhos, `aria-pressed` indica grupo para acessibilidade. Sem mudança em `template.json`, `render`, `bridge`, `Python/Pillow`, presets, escala/rotação, arquivo JPEG ou SóClick.

## Invariantes contratuais
- `templates/chaveiro-3x4/template.json` permanece **bit a bit** igual ao SHA na base (auditar por `git diff --exit-code BASE..HEAD -- templates`).
- Folha **216×152 mm**, saída **2551×1795 px @ 300 DPI**, 18 slots 6×3 em **34×44 mm**; coordenadas e cabeçalho de cliente permanecem intactos.
- `duplicateSelectedSlots`: usa ordem física dos slots, procura vazios após maior índice selecionado (depois wrap-around), nunca sobrescreve slots ocupados; cópia inclui source, pan, escala e ângulo. Se não houver vazios suficientes, copia só os que cabem e informa quantidade sem duplicação.
- Duplicação individual do chaveiro continua com regra original `slot_N → slot_(N+1)`; não mudar essa sem outra solicitação explícita.
- Seleção visual é estado do React, nunca gravado no manifesto, output, SQLite ou API.

## Execução no Windows (Antigravity, não confiar em memória)
1. `git status --short --branch`; `git rev-parse HEAD`; `git worktree list`; `git fetch origin`. Não substituir worktree ativo nem descartar arquivo alterado. Criar worktree isolado baseado em `origin/codex/keychain-multiselect-dblclick-ux-20261015`.
2. Verificar arquivos alterados e nenhuma geometria: `git diff --stat origin/codex/soclick-operational-readiness-20261015...HEAD` e `git diff --exit-code origin/codex/soclick-operational-readiness-20261015...HEAD -- templates apps/desktop`.
3. Executar sem inventar PASS:
   ```powershell
   npm --prefix apps/ui test -- --run
   npm --prefix apps/ui run build
   .\.venv\Scripts\python.exe scripts/verify_repo.py
   .\.venv\Scripts\python.exe -m pytest -q tests/test_annotations.py tests/test_render.py
   ```
   Se os comandos diferirem, inspecionar os scripts reais. Não testar impressão física só para validar UI.
4. Em execução local pelo app DESKTOP (não apenas Vite no navegador), importar **duas fotos de teste** com 18 slots na grade. Atribuir fotografias com `source_id` diferentes e zoom, pan e rotação diferentes nos slots #01/#02/#03. Usar Shift para selecionar #01, #02, #03; confirmar **#03 azul, #01/#02 vermelho**. Clicar #01 (sem Shift) deve torná-lo azul e manter #02/#03 em vermelho; duplo clique em #02 deve criar #04/#05/#06 (3 fotos e enquadramentos correspondentes) e marcar os novos destinos. Contar **um único Undo** para desfazer todo o lote.
5. Clicar slot único preenchido e duplo clique: apenas duplicação individual original. Testar última célula; testar 3 slots com alguns destinos ocupados e capacidade insuficiente; não sobrescrever itens existentes em lote.
6. Verificar overlay em cima das fotografias e do placeholder; arraste, zoom via roda, escala pelo slider e drop continuam funcionando (pointer-events none). Quando troca para Globo, Calendário ou Manager, nenhum overlay vermelho deve aparecer.
7. Capturar 2 screenshots (com PII ocultada) e, se viável, uma gravação de 10s demonstrando Shift+clique/duplo clique; registrar logs de Console apenas se aparecerem erros reais, sem dados de cliente.
8. Renderizar UM JPEG **local** de teste antes/depois e comparar `canvas_size_px`, DPI e metadados físicos. Ao comparar pixels, só esperar igualdade se estado/sources forem os mesmos; seleção não entra no JPEG. Não enviar à SóClick, não usar flags de produção e não modificar photos originais.
9. Medir número de objetos Fabric, FPS de gesto e quantidade de renders usando mecanismos já existentes se disponíveis; evitar fazer loops de benchmark ou refatorar engine. Rodar suíte completa UMA VEZ por alteração, testes focados para diagnóstico.
10. No final COMENTAR na PR do recurso, e apresentar perguntas ao ChatGPT (seções abaixo).

## Devolutiva obrigatória para ChatGPT (comentário GitHub)
- (1) O que entendi do fluxo `mousedown→dblclick→React selection→duplication→undo→Pillow`;
- (2) arquivos e funções reais, versões do Fabric 7.4 / React 19, SHAs e worktree;
- (3) execução dos testes (comando, PASS/FAIL/NOT_RUN, traceback);
- (4) provas da tela azul/vermelho (com screenshots sem PII) e três fotos duplicadas;
- (5) comparação `templates`/render intactos;
- (6) defeitos observados e correções com commit (somente se reproduzidos);
- (7) recomendações de UX posteriores, evitando aumentar escopo;
- (8) perguntas: `ChatGPT, revise estes testes e diga se podemos integrar a PR à branch operacional; aguardarei orientação.`

**Logs de `status-evydflow.ps1`, PIDs da API e worker em 8095 NÃO validam esta interação de interface.** Os prints do gerador e testes de Fabric são a fonte de evidência; `provider_delivery_verified=false` significa que envio físico não foi certificado e não é objetivo desta PR.
