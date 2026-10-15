# Auditoria operacional integrada — Print Generator + SóClick / Windows 11 Home
Data: 2026-10-15 • Branch `codex/print-generator-operational-recovery-20261015` • Base PR #28 `25382d60`.

## 1. Evidência e limites
- Antigravity relatou [homologação PR #28, commit 25382d60](https://github.com/hypeneural/evydencia-print-generator/pull/28#issuecomment-6196653819): 296 Vitest, 214 Pytest, teste visual do Chaveiro e JPEG 2551×1795 px, 300 DPI. O CI remoto da base também passou. Fotos/JPEG em `file:///C:/...` não são inspecionáveis pelo revisor remoto.
- O relato testa gestos e JPEG **naquela sessão**. Não demonstra restart do Windows, fechamento abrupto do app, perda de alimentação, perda de internet, retomada de edição inacabada, recuperação do worker ou confirmação do laboratório.
- Verificação do código: `ProductCanvas.tsx` (Fabric/overlays HTML), `App.tsx` (estado React e UI), `DesktopBridge` (snapshot da geração), `render_receipt.py` (SHA-256 em memória por sessão), `render/output.py` (arquivo em disco), `soclick/client.py` (POST idempotente por hash), `soclick/discovery.py` (GET loopback).
- **Limitação real:** sources importados, transformações não exportadas e último `RenderReceipt` vivem em memória. Fechar/reiniciar NÃO restaura o projeto automaticamente. A imagem JPEG já salva continua no disco, mas o handoff da sessão antiga precisa de nova geração após reinício. A próxima feature deve ser um *projeto recuperável* com manifesto, proveniência e revalidação dos arquivos fonte, não um simples `localStorage` com paths privados.
- `127.0.0.1:8095` é loopback local, não requer acesso à internet externa. Preparação de rascunho pode funcionar offline **se EvydFlow local e os diretórios estiverem disponíveis**; comunicação remota com o laboratório depende da rede e ocorre depois, no EvydFlow.

## 2. Fluxo verdadeiro e propriedade dos estados
1. Operador edita/duplica fotos localmente em React/Fabric. Contornos azul/vermelho pertencem só à prévia. `template.json` e `Pillow` fixam a arte industrial.
2. Geração Python grava um JPEG. Recebimento do objeto `RenderResult` é evidência **somente de arquivo local gerado**. Falha posterior na SóClick não apaga o arquivo.
3. Python conserva `RenderReceipt(output_path, edit_state, snapshot, sha256)` por sessão e rejeita foto/JPEG alterados após gerar.
4. Gerador descobre EvydFlow por 2 GETs loopback e executa `POST /api/soclick/intake/print-generator` autenticado. HTTP 200 válido mais `job_id`/URL válidos confirmam um **rascunho** local na SóClick, não upload remoto e muito menos produção física.
5. EvydFlow valida origem, `EVYDFLOW_OPERATOR_API_TOKEN` e `EVYDFLOW_ALLOWED_ROOTS` (PR #41 já incorporada no fluxo EvydFlow), copia conteúdo autorizado e cria DRAFT no próprio SQLite. O JPEG pode estar fora de raízes configuradas após boot; isso produz recusa, não falha de render.
6. Editor SóClick, fila e worker têm etapas diferentes: revisão, upload e reconciliação GET 7/7, autorização física por pedido, envio e recibo externo. Não remeter automaticamente após um timeout.

## 3. O que foi melhorado neste patch
- Tratamento Python por códigos estruturados: `ROOTS_NOT_CONFIGURED`, `OPERATOR_NOT_AUTHORIZED`, `PANEL_OFFLINE`, `HANDOFF_UNCERTAIN`, `HANDOFF_REJECTED`, `RENDER_CHANGED`.
- UI agora diz **Arquivo salvo no computador**, com o botão **Abrir pasta**. Mensagens amigáveis explicam que a falha da SóClick não destruiu o JPEG, com próximo passo específico em vez do HTTP cru. Em falha incerta pede consultar o painel antes de repetir, sem retry automático.
- Feedback é multilinha e responsivo; botão **Preparar na SóClick** distingue rascunho de impressão física; "Fotos na folha" e "espaço livre" substituem termos técnicos.
- Nenhum script faz restart automático, POST adicional, muda env vars, exporta tokens, modifica banco real ou imprime fisicamente.

## 4. Mensagens simples / contrato de UX
| Evento | Usuário deve ler | Próxima ação |
|---|---|---|
| JPEG criado | Arquivo salvo no computador | Abrir pasta ou preparar rascunho |
| SóClick 503 / raízes ausentes | O arquivo foi salvo, mas a SóClick ainda não está pronta | Gestor autoriza **somente a pasta de fotos usada**, no ambiente do EvydFlow |
| Credencial inválida | Este computador não tem acesso à SóClick | Gestor verifica autorização sem mostrar o token |
| Painel local parado | Painel SóClick não está disponível neste momento | Verificar se o EvydFlow correto está ativo |
| Timeout / status incerto | Não sabemos se o rascunho chegou | Conferir rascunho no painel; NÃO reenviar automaticamente |
| Rascunho aceito | Rascunho salvo na SóClick | Conferir fotos/cópias/medidas; não foi impresso |
| Foto mudou após gerar | As fotos ou o arquivo mudaram após a geração | Gerar novamente |
| Folha cheia | A folha está completa; nenhuma foto foi substituída | Remover/alterar seleção, nunca substituir silenciosamente |

Não mostrar stack trace, caminhos completos de clientes, token de operador, HTTP 503 ou `EVYDFLOW_ALLOWED_ROOTS` na interface do operador. No diagnóstico técnico, não imprimir os valores de segredos.

## 5. Ciclo de vida Windows 11 Home
**Fechar janela:** `window.events.closed`/finalização de `webview.start` acionam cleanup Python (`PreviewService.shutdown` e `AssetServer.stop` no `finally`). O estado de edições não exportadas não é durável. Não afirmar recuperação de projeto.

**Reabrir o programa:** importação/registro de fotos começa novamente; templates e UI local devem carregar mesmo sem internet. `RenderReceipt` antigo não é reaproveitado. Não tentar preparar um caminho antigo sem gerar e validar novamente.

**Reboot/logon:** Windows `AtLogOn` do EvydFlow é tentativa de boot **no logon**, não supervisão permanente; `AtStartup` dispararia no início do Windows, mas isso não prova que um processo filho sobrevive a falhas. A documentação Microsoft diferencia os gatilhos e recomenda salvar estado para reinício; não instalar tarefa para o editor automaticamente. Confirmar PID/worktree/config efetivamente herdada antes de recuperar worker.

**Internet desconectada:** geração/preview e JPEG locais continuam. Ao preparar, a API loopback só funciona se o EvydFlow e a rede local estiverem íntegros; envio remoto para laboratório pode ficar aguardando e precisa de conciliação no EvydFlow. Não tratar perda de internet como duplicação automática.

**Energia cortada:** o sistema não pode garantir zero perda de edição não exportada. Testar somente sob janela aprovada; não interromper um banco SQLite WAL ativo artificialmente. Sempre considerar outcome remoto incerto depois de reconectar.

Fontes oficiais:
- Microsoft PowerShell 5.1, `-AtLogOn` versus `-AtStartup`: https://learn.microsoft.com/en-us/powershell/module/psscheduledjob/new-jobtrigger?view=powershell-5.1
- Microsoft Windows recovery / Restart Manager: https://learn.microsoft.com/en-us/windows/win32/recovery/using-application-recovery-and-restart
- pywebview 6 events, `loaded`, `closing`, `closed`: https://pywebview.flowrl.com/api/
- SQLite WAL durability/network filesystem: https://sqlite.org/wal.html

## 6. Gates físicos locais, em ordem (Antigravity)
1. Isolar worktree `origin/codex/print-generator-operational-recovery-20261015`; checar `git status`/SHA. Não limpar checkout operativo.
2. Executar CI local `npm --prefix apps/ui test -- --run`, `npm --prefix apps/ui run build`, `.\.venv\Scripts\python.exe -m pytest -q`, `.\.venv\Scripts\python.exe -m ruff check .`, `.\.venv\Scripts\python.exe scripts/verify_repo.py`. Marcar PASS/FAIL/NOT_RUN reais.
3. Usar 3 fotos **sintéticas** Chaveiro #01/#02/#03 com enquadramentos distintos, duplicar 3 com Shift e duplo clique; Ctrl+Z uma vez reverte lote, folha 18/18 não sobrescreve.
4. Salvar JPEG, confirmar caminho/DPI/dimensões, simular **somente** EvydFlow indisponível sem encerrar processo real: mock ou instância isolada. Confirmar "Arquivo salvo" e orientação legível; reabrir pasta.
5. Simular 503 com `EVYDFLOW_ALLOWED_ROOTS` ausente **num EvydFlow isolado e sintético**, não desconfigurar o processo canônico: mensagem para gestor, arquivo no disco. Testar 403 e timeout incerto por mock, sem repetir POST automaticamente.
6. Tirar rede **somente com aprovação**, preferindo notebook/ambiente de teste: o editor local e exportação devem funcionar offline; checar UI e retorno; reconectar e consultar status, sem física.
7. Fechar e reabrir app após gerar um JPEG; validar arquivo original persistente e mensagem de que o projeto em memória precisa ser reaberto, se aplicável. NÃO afirmar recuperação de enquadramento enquanto não houver função persistente.
8. Para reboot real, confirmar nenhuma fila/pedido físico em voo, obter autorização e janela; verificar execução do EvydFlow e tempo medido de partida sem criar worker duplicado.
9. Benchmark de abertura, render local e latência com valores medidos; não afirmar 60 FPS ou 100% disponibilidade por inspeção de código.
10. Responder em comentário da PR com evidências, comandos, logs sanitizados, cinco UX scenarios e limitações de recuperação. **Não fazer merge automático ou impressão física.**

## 7. Próximo projeto arquitetural (NÃO IMPLEMENTADO)
Persistência durável de edição: autosave atômico + manifesto de fontes (caminho/canonical ID/hash/mtime), reimportação segura/relacionamento do registry, schema versionado, recuperação explícita após crash, autorização dos arquivos locais, TTL/limpeza, proteção de PII e teste de corte de energia. Não salvar apenas a seleção em `localStorage`, isso não restaura `SourceRegistry`. Separadamente, supervisor Windows para EvydFlow deve validar PID e SQLite canônico e nunca realizar retry físico incerto.

## 8. Revisão independente pós-homologação Antigravity (PR #29)
O [comentário de homologação #6198992239](https://github.com/hypeneural/evydencia-print-generator/pull/29#issuecomment-6198992239) descreve 304 Vitest, 221 Pytest, 3 jobs de CI por execução e cenários por Chrome DevTools. **Os jobs são confirmáveis no GitHub; as fotos/capturas em `file:///C:/...` e a sessão nativa completa não foram inspecionadas independentemente.**

### Divergências factuais encontradas no código
- **HTTP 500 não é `HANDOFF_REJECTED`.** O cliente o classifica como `HANDOFF_UNCERTAIN` (possível DRAFT com resposta incompleta). `HANDOFF_REJECTED` cobre outros HTTP, como 400.
- **Falha de conexão resetada após POST não é o mesmo que conexão recusada.** A implementação anterior interpretava `URLError(ConnectionResetError)` como `PANEL_OFFLINE` e autorizava tentar de novo pelo texto. Corrigido: somente `ConnectionRefusedError` é `PANEL_OFFLINE`; timeout, reset, pipe rompido e erros de transporte não confirmados resultam em `HANDOFF_UNCERTAIN`.
- **Orientação não era bloqueio técnico.** Mesmo após um resultado incerto o botão Preparar continuava ativo. Corrigido: requer um reconhecimento explícito de que o operador conferiu no painel que o DRAFT não existe, antes de liberar outro POST. A caixa de seleção não executa POST. Não é garantia absoluta contra usuário que confirma sem conferir.
- **Erro Python inesperado vazava detalhes brutos via objeto JSON do pywebview.** Corrigido: resposta agora é sanitizada e `HANDOFF_UNCERTAIN`, com stack apenas no log local.
- **A velocidade de build Vite não mede o tempo de abertura do executável pywebview** e `pointer-events: none` não torna overlays HTML de custo zero. O relato de 60 FPS sem amostras `requestAnimationFrame`/traces permanece **não auditado**.
- **960×700 px no Chrome é simulação**; `app/window.py` fixa largura mínima **1024** e altura mínima **680** para o desktop nativo. Não chamar isso de homologação de janela desktop abaixo da largura mínima.

### Divergência de dependências instaladas
No relatório local constam `Pillow 11.1.0` e `React 19.0.0`, mas o repositório exige **`Pillow>=12.3,<13`** em `pyproject.toml` e declara `react: 19.3.0` em `apps/ui/package.json`. É possível que o relatório contenha números copiados de outro ambiente; **é obrigatório medir na instância que efetivamente executa o app**. Adicionado `scripts/audit_win11_print_generator_runtime.py` (somente leitura, stdlib) com checagem real das restrições Python/Pillow/pywebview. Para frontend: `npm --prefix apps/ui ls react react-dom vite fabric --depth=0`; o retorno real não pode ser inferido do manifesto. Se a venv instalada usa Pillow 11.1, atualizar em ambiente de teste com versão compatível **antes** de aprovar release; não ajustar o pin para validar artificialmente versão velha.

### Matriz residual de indisponibilidade e segurança
- Rascunho confirmado / browser fechado: abrir URL do rascunho no painel, não disparar outra importação para compensar janela.
- DRAFT de status incerto: consultar pelo idempotency_key / SHA do JPEG no painel/camada operacional. Nova tentativa **somente** após reconciliação; o checkbox apenas documenta a verificação humana.
- `EVYDFLOW_ALLOWED_ROOTS` no ambiente herdado pela **API EvydFlow** continua sendo a causa do HTTP 503 real anterior. Mensagem amigável **não configura** a pasta autorizada. A pasta de saída pode variar com a foto primária: autorizar apenas diretórios canônicos, testando USB/Downloads não permitidos.
- Falta de internet externa **não significa** indisponibilidade de `127.0.0.1:8095`; upload remoto ao laboratório depende de rede e de worker/reconciliação próprios.
- `AtLogOn` garante apenas um disparo por logon, não supervisiona o processo para sempre. Backup/recuperação de edição não exportada **ainda não existe**: não declarar garantia após reboot/queda de energia, e não salvar tokens/fotos brutas em `localStorage`.

### Gates adicionais para Windows 11 Home
1. Confirmar worktree de origem e hash da PR, rodar `.\.venv\Scripts\python.exe scripts/audit_win11_print_generator_runtime.py` e `npm --prefix apps/ui ls react react-dom vite fabric --depth=0`; se houver versão divergente, classificar **FAIL** e registrar qual executável, sem instalar em produção durante a auditoria.
2. Testar **também** `URLError(ConnectionResetError)`, `URLError(BrokenPipeError)`, refused e timeout no Python, e garantir que só recusada prova PANEL_OFFLINE. Não executar POST em produção durante simulação.
3. Na interface nativa, induzir HANDOFF_UNCERTAIN via serviço **isolado**, confirmar botão desativado, checar no painel sintético DRAFT ausente, marcar checkbox e provar que só então uma tentativa manual fica habilitada. Testar duplo clique rápido durante preparo: no máximo **um POST** em voo.
4. Emitiu DRAFT? Conferir o rascunho pelo `job_id` e status, sem inferir envio ao laboratório.
5. No relatório final diferenciar **PASS em CI**, **PASS no aplicativo nativo**, **PASS no Vite/Chrome** e **NOT_RUN** com dados reais. Não afirmar 60 FPS sem medição, nem autosave sem restauração após crash.
