# Auditoria P0 — SóClick numa estação Windows 11 Home (uma pessoa, sem etapas manuais repetidas)
**Data:** 2026-10-16 | **PRs:** Gerador [#30](https://github.com/hypeneural/evydencia-print-generator/pull/30) + EvydFlow [#42](https://github.com/hypeneural/evydflow/pull/42).
**Importante:** documentação do fluxo de DRAFT; NÃO certifica impressão física/fornecedor. Trabalhos locais no Windows não foram repetidos pelo auditor remoto.

## Interpretação operacional correta
A pessoa que abre o Gerador é a mesma que produz, ajusta os templates e confere SóClick. O seletor visual agora apresenta **Produção** / **Configurações** em vez de cargos `Operador` / `Gestor`; estados internos `operator` / `manager` continuam por compatibilidade com domínio e testes. Isso não constitui autenticação nem controla permissões do laboratório.

### Caminho feliz
1. Windows 11 inicia; Task Scheduler `EvydFlow - Iniciar Servicos ao Entrar` no logon (não necessariamente antes de fazer login) chama o boot canônico. O boot e o start direto executam de forma idempotente `configure-print-generator-handoff.ps1 -Apply`, que só cria `C:\Evydencia\print-generator-handoff` e adiciona **uma chave fixa** em `C:\Evydencia\secrets\pilot-context.env`, com backup atômico e preservação de metadados ACL. Não abre raiz `C:\` para o processo servidor. Controles de credenciais e caminhos DB permanecem.
2. O Gerador permite fotografias de qualquer pasta acessível à conta do Windows, inclusive unidades diferentes; os originais não são movidos. Render PDF/imagem não sofreu alteração. O JPEG final mantém nome, tamanho, perfil, cores, DPI e SHA capturado.
3. Ao clicar `Gerar e preparar` ou `Preparar na SóClick`, o bridge valida o recibo do JPEG e **se o painel estiver offline tenta a recuperação segura antes do primeiro POST**, via task agendada verificada e fallback `recover-api.ps1` sem `-AllowForceStop` ou `-ReloadOwnedApi`. Não há necessidade de botão separado para primeiro start. O botão `Reativar` permanece só para diagnóstico/fallback e não transmite DRAFT.
4. Cópia SHA-verificada somente do JPEG final na pasta fixa (não dos arquivos originais). `POST /api/soclick/intake/print-generator` só acontece uma vez, com idempotency_key e token; o EvydFlow cria DRAFT no `EVYDFLOW_SOCLICK_DB_PATH` e abre `/panel/soclick?focus=job_...#review`.
5. DRAFT salvo é diferente de envio físico; flags de impressão real continuam `0`. Em timeout/reset `HANDOFF_UNCERTAIN`, não reenviar automaticamente; conferir rascunho pela chave e no banco. Não transformar correção de conexão em reenvio do pedido.

### Casos especiais — comportamento honesto
- API **já ativa** em versão anterior, sem `EVYDFLOW_ALLOWED_ROOTS`: a instalação automatizada na inicialização nova não muda o ambiente de processos **já executando**. Precisa uma migração de uma só vez, com mudança do checkout e restart API autorizado em janela sem operações ativas. Não afirmar que apenas fechar e abrir Gerador corrige.
- API caiu **com worker vivo**: boot canônico recusa duplicação e o bridge usa supervisor API-only só se a task inicial foi verificada. Mutex, ownership, PIDs, pulse e console são inspecionados; o script pode recusar para proteger fila. Não é autorrecuperação ilimitada.
- Sem task, configuração inválida, ausência de token, ACL negada ou script adulterado: fail closed, preservar JPEG original; não desativar autenticação nem liberar todo o disco.
- Windows sem conexão externa: loopback e render podem continuar; provedor remoto pode permanecer offline. Nenhuma publicação física é prometida sem confirmação do backend.
- Notebook suspenso/hibernado: task `AtLogOn` não substitui gatilho de retomada; o primeiro preparo faz recuperação local sob demanda. Não há autosave completo do edit-state em fechamentos abruptos.

## Banco e fila: fatos a reconfirmar no host
O Antigravity relatou `soclick_jobs.db` com `READY_FOR_PRODUCTION` sem envio físico e `ack_failed` sintéticos/terminais; são evidências locais, não substituem leitura atual de `jobs`, `job_manifests`, `print_items`, `source_files`, leases, fila, heartbeat, `services_pids.json` e `production_outbox` antes de restart real. O supervisor versionado guarda PID worker e recusa escopo estranho, mas seus testes mock/portas efêmeras não provam o runtime canônico 8095.

## Homologação mínima sem loops
- Print Generator: `python -m pytest -q tests/test_soclick_automatic_recovery.py tests/test_soclick_handoff.py tests/test_soclick_staging_and_recovery.py`, `python -m ruff check .`, `npm --prefix apps/ui test -- --run`, `npm --prefix apps/ui run build`. Usar CI quando verde, sem repetir suítes completas sem mudanças.
- EvydFlow: parser AST do Windows PowerShell 5.1 para os três scripts de boot/setup e `recover-api.ps1`, `pytest -q tests/unit/test_win11_recover_api_supervisor.py tests/unit/test_win11_print_generator_root_boot_contract.py`, segurança HTTP.
- Provar setup idempotente: primeiro boot adiciona chave somente se ausente, segundo boot não modifica hash de arquivo nem cria novos backups; credenciais e ACL permanecem; diretório normal sem link.
- Provar recuperação pre-POST: offline+task correta=>uma só tentativa de recovery e no máximo um POST; API saudável=>zero task e um POST; task errada=>zero POST; POST timeout=>nunca repetir silenciosamente.
- Provar canário de DRAFT sintético num **Windows real** depois de aprovação da mudança de configuração e restart; conferir SHA, DB canônico, `is_existing`, link e autenticação. Separar canário de envio físico.
- Abrir pywebview nativo no notebook Avell, medir frio/quente, 125% display, tamanho mínimo, zoom, atalhos e UI de `Produção/Configurações`. Medir memória/uso CPU e disco; não prometer 60FPS sem profiler.

## Docs oficiais consultadas
- Microsoft `schtasks /run`: https://learn.microsoft.com/windows-server/administration/windows-commands/schtasks-run
- Task Scheduler logon/start triggers: https://learn.microsoft.com/windows-server/administration/windows-commands/schtasks-create
- Win32 console process groups: https://learn.microsoft.com/en-us/windows/console/generateconsolectrlevent
- GetConsoleProcessList buffer: https://learn.microsoft.com/en-us/windows/console/getconsoleprocesslist
- NTFS ACL and file rights: https://learn.microsoft.com/en-us/windows/win32/fileio/file-security-and-access-rights
- .NET `File.Replace` metadata/backup: https://learn.microsoft.com/dotnet/api/system.io.file.replace
