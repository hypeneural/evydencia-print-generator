# P0 — Print Generator → SóClick: handoff unificado e recuperação Windows 11 Home

**PRs pareadas:** Print Generator #30 (base #29), EvydFlow #42 (base #37). **Status:** implementação sob homologação; não houve merge, restart ou envio físico no host Windows.

## Constatação forense (sem adivinhar a configuração)
O operador visualizou "O arquivo foi salvo, mas a SóClick ainda não está pronta" após gerar um JPEG do Calendário 2027. A geração Pillow funcionou: o erro é da **fase separada de importar DRAFT**. O endpoint real `POST /api/soclick/intake/print-generator` em `evydflow/api/soclick_routes.py` chama `require_print_generator_allowed_roots()`, que retorna HTTP 503 **antes de criar o job** se `EVYDFLOW_ALLOWED_ROOTS` faltar no processo EvydFlow em perfil production. A task AtLogOn `services/boot-evydflow.ps1` não carregava essa chave de `pilot-context.env`, mesmo com API/worker ativos. Isso é diferente de erro de rede, permissão de token, arquivo apagado ou indisponibilidade do laboratório externo.

Os DRAFTs reais pertencem ao **SQLite `EVYDFLOW_SOCLICK_DB_PATH`**, no cenário Windows anterior `C:\Evydencia\evydflow-soclick-ops\data\soclick_jobs.db`. Não interpretar `production.db` ou `outbox.db` como comprovante desse DRAFT. Jamais inferir envio físico a partir de HTTP 200 do intake.

## Correção estrutural
1. O operador pode importar fotografias de qualquer pasta **que seu usuário Windows consiga ler** — HD local, rede/UNC, Downloads e unidade externa. Isso **não** significa liberar `C:\` na API.
2. O aplicativo gera o arquivo final normalmente perto da foto, com a mesma geometria física e ICC. `RenderReceipt` verifica snapshot imutável + SHA do JPEG. Para o handoff apenas, `soclick/staging.py` prepara **outra cópia byte-for-byte** numa raiz fixa, `C:\Evydencia\print-generator-handoff\SHA_PREFIX\SHA_COMPLETO\NOME_ORIGINAL.jpg`, com temp e `os.replace` no mesmo volume, verificando SHA de origem e destino.
3. O app nunca copia o original do cliente para a área de API. A cópia não altera o arquivo enviado à produção (mesmos bytes JPEG, DPI e ICC). Metadata `slots.original_path` é conservada para identificação de clientes e não é usada para fazer a API ler a origem.
4. EvydFlow PR #42 configura somente `C:\Evydencia\print-generator-handoff` no `pilot-context.env`, e os **dois** caminhos de inicialização (logon e manual) importam essa raiz antes de iniciar a API. Rejeitam caminho fora do escopo, arquivo de contexto linkado e pasta de preparo linkada.
5. A API local pode estar parada. Agora há um botão **Reativar painel SóClick** quando `PANEL_OFFLINE`. Um clique solicita apenas `schtasks.exe /Run /TN "EvydFlow - Iniciar Servicos ao Entrar"` **depois de verificar** task name, Executable e caminho do boot/cwd canônico. EvydFlow controla exclusão com mutex próprio e comprova PIDs; o Gerador NÃO inicia worker ou POST por conta própria.
6. Timeout, resultado desconhecido, reset após POST continuam exigindo reconciliação do DRAFT antes de outro POST. Nenhuma automação inicia envio pago, produção física, WhatsApp ou revelação.

### Por que não abrir autorização irrestrita
Um endpoint que aceita `output_path` informado pelo cliente e possui `EVYDFLOW_ALLOWED_ROOTS=C:\` poderia fazer o processo servidor ler dados de qualquer diretório acessível à conta do serviço. Ter um **staging único** mantém a experiência do operador com fotos de qualquer pasta, mas sem transformar o servidor local numa leitura arbitrária de disco. Isso também evita ter que editar a allowlist a cada cliente.

### Bootstrap inicial — execução somente no Windows real
No checkout do EvydFlow PR #42, depois de inspecionar tarefas, bancos e fila:
```powershell
powershell.exe -NoProfile -File .\services\configure-print-generator-handoff.ps1
# Após autorização explícita do gestor e conferência do DRY RUN:
powershell.exe -NoProfile -File .\services\configure-print-generator-handoff.ps1 -Apply
```
Esses comandos **não reiniciam** serviço nem alteram os flags de produção. O operador deverá planejar a reinicialização segura da API na instância correta para que a nova variável seja herdada, sem processos duplicados nem tarefas incertas. Verifique `services/status-evydflow.ps1 -Port 8095 -Json` e o DB canônico antes/depois.

## Gates obrigatórios locais
- Atualizar **ambos** os worktrees isolados; confirmar HEAD, `git status`, pasta aberta pelo executável e webview asset build. **Não** substituir `main` ou worktrees que têm fotos e mudanças.
- Print generator: `npm --prefix apps/ui test -- --run`, `npm --prefix apps/ui run build`, `.\.venv\Scripts\python.exe -m pytest -q`, `.\.venv\Scripts\python.exe -m ruff check .`, `.\.venv\Scripts\python.exe scripts/verify_repo.py`. EvydFlow: teste focado Windows task/roots e parse AST PowerShell 5.1 para scripts alterados.
- Gerar JPEG de teste com origem fora da raiz; confirmar hash da origem e da cópia em `print-generator-handoff` idênticos, foto original não copiada, nome preservado e zero alteração nas medidas / pixels / DPI.
- Sem configurar raiz, simular 503 em API isolada; após autorização e **restart controlado**, POST com arquivo staged deve retornar DRAFT 200/201, job_id válido, e aparecer no **soclick_jobs.db** canônico. Conferir `is_existing` em replays por SHA.
- Com API offline, clicar Reativar; task certificada pode inicializar de forma idempotente. Task ausente, worktree errado, ação modificada ou porta ocupada por outro serviço => aviso sem executar comandos desconhecidos. Com API já ativa, não executar schtasks.
- Desconectar internet externa somente num teste autorizado: geração JPEG e API loopback podem continuar; upload remoto é OUTRA fase. Não forçar reboot se existirem jobs pagos ou filas pendentes.
- Medir cold/warm start de WebView2, tempo para gerar JPEG, memória e FPS com profiler; não inferir 60 FPS por `pointerEvents:none`.
- Reboot ou fechamento abrupto **não restaura edição inacabada**: autosave está fora do escopo. Persistência do JPEG gerado não prova retomada de edição.
- Confirmar build UI, ícone de reativação e textos acessíveis na janela nativa mínima 1024x680 e com zoom de exibição 125%.

### Organização e próximo passo
PRs empilhadas do Print Generator: #27 → #28 → #29 → #30. EvydFlow: PR #37 como base, PR #42 como patch isolado. Não integrar #30 na main antes de suas bases e da homologação de integração com a PR #42. Não abrir novas branches para cada teste; atualizar PR de origem e registrar evidências numa única conversa.

Referências oficiais: [Microsoft schtasks run](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/schtasks-run), [Microsoft Task Scheduler](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/schtasks), [Python shutil / cópia em arquivos](https://docs.python.org/3/library/shutil.html), [SQLite WAL](https://www.sqlite.org/wal.html).
