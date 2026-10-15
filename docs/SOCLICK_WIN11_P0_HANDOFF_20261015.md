# Auditoria forense P0 — Print Generator ↔ EvydFlow ↔ SóClick
> **Instrução canônica para Antigravity 2.23.x / Gemini 3.8 Flash, Windows 11 Home**  
> **Não** usar outro checkout, memória antiga ou um checklist abreviado como autoridade. Não inventar validação.
>
> Print Generator base: `702d2ff71d7145115f8486c42cccbd66e0662557`; branch de correção: `codex/soclick-operational-readiness-20261015`, PR #27 para `feat/soclick-operator-handoff`.  
> EvydFlow release candidata: PR #37, branch `fix/p0-soclick-copy-order-crm-links-timeline-20261013`, observada em `5ce14e63fb745da545af797bd3980862980d2525`. **HEAD é mutável**: conferir novamente na execução. PR #37 continua DRAFT/NO-GO até gates reais.

## 1. Contrato operacional: entenda a sequência antes de executar

1. `App.tsx:executeRender(sendToSoclic)` decide gerar localmente ou também preparar um rascunho. O rótulo não deve confundir DRAFT com envio físico.
2. `bridge.renderJob(editState)` → `DesktopBridge.render_job` valida template e slots, resolve `SourceRegistry` e cria `JobSnapshot`.
3. `render/engine.py` compõe Pillow + cortes + anotação de chaveiro, resolve saída sem sobrescrever a fonte e grava JPEG atomicamente. Nenhum arquivo `templates/**/template.json` deve ser alterado.
4. **Nova barreira**: `RenderReceipt.capture` prende `output_path`, `EditState`, `JobSnapshot` e SHA-256 original à sessão. `prepare_soclic` não reconstrói o snapshot de uma UI potencialmente alterada; rejeita mudanças de enquadramento, JPEG substituído ou saída estranha antes do POST. **Não é ainda uma outbox durável entre reinícios do aplicativo.**
5. `soclick/discovery.py` exige `GET /health` e contrato coerente de `GET /api/soclick/environment` numa porta loopback. Isso não prova worker, banco igual ou route de intake; apenas elimina listeners triviais estranhos.
6. `soclick/client.py` calcula SHA, valida a assinatura esperada, monta slots originais, faz `POST /api/soclick/intake/print-generator`, exige resposta com job e URL local para esse mesmo job. Tentativa repetida não deve causar impressão.
7. `evydflow/api/soclick_routes.py` verifica requisição local; **P0 pendente**: unificar autenticação real do intake com as sessões protegidas de `production_routes.py`. O cabeçalho `x-evydflow-operator-token` enviado pelo cliente ainda não é validado nessa rota, no HEAD inspecionado. NÃO confundir loopback com autorização.
8. `evydflow/soclick/print_intake.py` confere caminho, tamanho, JPEG, SHA, monta grupos de cliente de slots, observação de até 135 caracteres, preset de papel/tamanho, staging/thumbnail e manifesto, então persiste rascunho local. Extração de pasta **não comprova validação CRM**; `crm_client` opcional não é injetado no intake atual.
9. O banco `soclick_jobs.db` cria `jobs` + `job_manifests` + `source_files` + `print_items` + `print_item_sources` + `job_events`. `job_id` é identidade local, `order_id` é identidade SóClick remota; `crm_order_uuid` pode estar nos metadados. Chaveiro pode conter múltiplos pedidos CRM em uma folha. **Não fazer join implícito por nome ou somente número humano.**
10. O retorno `panel_url` aponta `/panel/soclick?focus=<job_id>#review`; abrir navegador não é evidência de criação do job. Se navegador falhar, devolver link de conferência e manter o rascunho. O editor usa `draft_version` otimista; cópias, especificação e revisão são operações independentes.
11. Após revisão explícita, `drafts/{id}/submit` congela manifesto e coloca job em fila. **NÃO é equivalente a imprimir.** Worker de SóClick emprega CAS/leases/fencing; estados avançam `CREATED → PREPARING → PREPARED → ... → UPLOADING → RECONCILING → READY_FOR_PRODUCTION`.
12. Apenas consentimento físico e gates 7/7 permitem `SUBMITTED_TO_PRODUCTION`. Resultado de envio incerto precisa de conciliação; nunca reenviar automaticamente. Watchdog do worker monitora status remoto e registra `job_status_watches`.
13. O painel SóClick possui `GET /api/soclick/events/stream` SSE e eventos `job_events.seq`. O front usa `lastSeq` e debounce; o painel de produção usa polling a cada 3,5s com degradação para 15s na aba oculta. P0 futuro: reconciliar snapshot inicial, cursor e monitor sem duplicar chamadas remotas.

## 2. Autoridade, bancos e integridade

| Banco/objeto | Responsabilidade | Relacionamentos/verificações |
|---|---|---|
| SóClick `jobs` | Um job local, estado e referência | PK `job_id`, referência única, versão ativa do manifesto, `order_id` externo |
| `job_manifests` | Manifesto draft/frozen e hashes | `job_id` + versão; rejeitar mutação/versão errada |
| `print_items` | Arquivos, quantidade, papel, borda, progresso | FK `job_id`; cada item tem hash e estado independente |
| `source_files` + `print_item_sources` | Origem e relação item ↔ arquivo | Nunca confundir 18 slots do chaveiro com 18 pedidos ao laboratório |
| `upload_attempts`, `job_events` | Evidência, tentativas, história SSE | Event cursor por `seq`; `UNKNOWN_OUTCOME` nunca equivale a sucesso |
| `remote_snapshots` + `remote_snapshot_photos` | Autoridade do GET remoto completo | Comparação 7/7 de hash, bytes, cópias, tamanho, papel e borda |
| `job_status_watches` | Monitoramento remoto durável | Ligado a `job_id/order_id`; worker é responsável |
| `production.db` | Workflow de produção por CRM | `production_runs` (run_id) ↔ files/stages/events/artifacts/execution_requests |
| `outbox.db` | Entregas digitais e Z-API | `idempotency_key`; não repetir `sending/unknown_outcome` |
| `data.db` da fila | PersistQueue/worker | Não zerar, migrar ou copiar isoladamente sem plano de backup |

**Gaps forenses pendentes, NÃO resolvidos nesta PR**:
- Intake ainda não valida token de operador; autenticação deve ser corrigida no EvydFlow com testes contra requests de outro processo local, sem liberar chamadas cross-site.
- `print_intake.py` copia arquivo staged antes da transação do banco: quedas intermediárias podem deixar arquivos órfãos. Projeto de cleanup seguro requer inventário e leases, nunca exclusão cega.
- Idempotência deriva referência de `template_id` + prefixo do hash SHA-256 do JPEG; a chave do payload não é uma FK/índice independente de intenção do cliente. Auditar colisão e identidade entre lotes antes de mudar contratos.
- Sem prova de `crm_order_uuid` associada aos diferentes clientes em chaveiros, apresentar identificação como não verificada.
- `/health` não prova worker. O EvydFlow HEAD `5ce14e63` ganhou `worker_pulse.json` e rota protegida `/api/production/runtime/worker`, mas pulse recente não comprova proprietário de PID, mesmo banco ou fila processando.
- Um navegador aberto faz consultas remotas além do watchdog; não declarar status atualizado sem timestamp da observação.
- Reabrir gerador após reboot exige novo render até que exista outbox imutável persistente homologada. Não fingir retomada automática.
- Não editar a PR #37 nem iniciar uma segunda fila sem comunicar responsável pelo worktree atual.

## 3. Gates locais **em ordem**, sem ações físicas

### Etapa 0 — Identificar ambiente e preservar trabalho
```powershell
git status --short --branch
git rev-parse HEAD
git fetch origin
git diff --stat
git worktree list
```
Usar novo worktree limpo da PR #27 ou pedir autorização para mudar o checkout. NÃO `reset --hard`, `clean`, `restore`, checkout sobre alterações locais ou troca silenciosa da PR #37. Verificar Windows 11 Home, versões Python/Node/npm, build e caminho que o aplicativo aberto usa de fato.

### Etapa 1 — Testes de código do Gerador
No diretório `evydencia-print-generator`:
```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_render_receipt.py tests/test_soclick_handoff.py tests/test_soclick_runtime_audit.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
npm --prefix apps/ui test
npm --prefix apps/ui run build
```
Não declarar PASS se comando não rodou. Registrar código de saída e quantidade real de testes. Se comando variar, confirmar scripts no `pyproject.toml`/`apps/ui/package.json`; não improvisar dependências nem alterar versões sem diagnóstico.

### Etapa 2 — Auditoria read-only do Windows
Não inferir caminho do banco a partir do checkout: resolver a variável `EVYDFLOW_SOCLICK_DB_PATH` no processo **sem publicar segredo ou path privado**. Identificar listener na 8095, PID e CommandLine via WMI, diretório do processo, `services_pids.json`, task Agendada, API, worker e hash HEAD. Identificar se a API pertence à PR #37 correta e se há instância duplicada.
```powershell
.\.venv\Scripts\python.exe scripts\audit_soclick_runtime.py --port 8095 --evydflow-root "<PASTA_EVYDFLOW_CANONICA>" --soclick-db "<SOCLICK_DB_CANONICO>"
```
Script é somente-leitura; exige SQLite válido v11 com tabelas esperadas. Pulse recente é evidência parcial; PID deve ser validado pelo Windows. Nunca colocar tokens em parâmetros/prints nem disponibilizar conteúdo de clientes. Se SQLite desatualizado: **NÃO migrar nem resetar**, apenas reportar.

### Etapa 3 — Ensaios herméticos (sem laboratório)
- Rota estranha `/health` na 8090: rejeitar.
- API correta 8095: reconhecer somente após verificar contrato.
- Offline: mostrar erro útil sem perder JPEG; não iniciar automaticamente trabalhadores.
- Gerar com dados sintéticos, alterar zoom depois, preparar: **bloquear**. Gerar novamente, preparar: avançar.
- Alterar bytes do arquivo gerado: bloquear antes de POST.
- Simular URL remota maliciosa no retorno: nunca abrir navegador.
- Criar um único DRAFT local de teste, abrir a conferência, repetir mesmo JPEG: mesma referência e `job_id`; nunca submeter fisicamente.
- Falha de abertura do navegador: DRAFT mantém-se válido e exibe link.
- Verificar `draft_version`, referência, cópias, presets e observação em chaveiro com clientes sintéticos.
- Consultar eventos e worker/pulse read-only; console e UI devem distinguir rascunho, fila, verificação, confirmação remota e envio físico.
- Sem dados artificiais indisponíveis? Marcar NOT_RUN e explicar, nunca substituir por pedido real #5022.

### Etapa 4 — GO / NO-GO
PR #27 e PR #37 devem permanecer DRAFT/NO-GO enquanto houver falha CI, diferenças entre bancos/porta, autenticação sem validação, operação real não homologada ou ausência de evidências. Não habilitar `AllowRealProduction`, não usar `/enviar`, não reiniciar/encerrar worker e não fazer backup/restore automático no banco ativo.

## 4. DEVOLUTIVA OBRIGATÓRIA — **CONVERSAR COM CHATGPT NA PR #27**
Ao finalizar, publique **UM comentário na conversa da PR #27** (não apenas um arquivo ou commit), e mencione a PR #37 como referência cruzada. Use EXATAMENTE as seções abaixo, preenchidas com provas reais. Se algo não foi visto, escreva `NOT_RUN`/`NÃO SEI`. Não redija um resumo genérico:

```markdown
## DEVOLUTIVA AO CHATGPT — Antigravity 2.23.x / Gemini 3.8 Flash — YYYY-MM-DD HH:mm (Brasília)
### 1. O que eu entendi (explicação técnica com minhas palavras)
- Caminho completo desde o clique no Print Generator até DRAFT, fila, 7/7 e possível impressão.
- Diferenças entre arquivo JPEG, manifesto, pedido CRM, SóClick job, pedido remoto e prova de laboratório.
- Onde exatamente o servidor/worker Windows é iniciado e como detectei uma instância legítima.

### 2. Banco e relacionamentos que eu conferi DE VERDADE
- SQLite canônico (identificador redigido), schema_version, tabelas verificadas, FKs/índices.
- Onde run_id, job_id, crm_order_uuid e order_id são gerados/usados; lacunas encontradas.
- Qual consulta/comando prova a identidade (sem PII e sem segredos).

### 3. Repositórios, SHAs e ambiente
- Print Generator HEAD/branch/dirty/worktree, EvydFlow HEAD/branch/dirty/worktree, versão Windows/Python/Node/Antigravity.
- Porta, PID/CommandLine sanitizados, worker heartbeat e API; status do CI.

### 4. Matriz de testes (com provas)
| Teste/Comando | PASS/FAIL/NOT_RUN | Evidência resumida | Bloqueador |
|---|---|---|---|
| ... | ... | ... | ... |
- Casos negativos: arquivo alterado, mudança de enquadramento, porta errada, servidor offline, URL indevida.
- Evidência de idempotência e navegação para rascunho (se autorizado testar).

### 5. O que alterei e por quê
- Commits, arquivos, testes, DDL, contratos, impacto em produção; links das mudanças.
- Se não alterei algo, explique o motivo e a dependência.

### 6. Problemas e riscos que ainda observei
- Separar fatos reproduzidos de hipóteses, com caminho:linha.
- Comportamento do Windows local que ChatGPT ainda não consegue observar.

### 7. MINHA PROPOSTA DE PRÓXIMO PASSO
- Mudança mínima sugerida, testes necessários, GO/NO-GO explícito.
- Não começar produção paga por conta própria.

### 8. PERGUNTAS PARA CHATGPT
- 2 a 5 perguntas concretas, ou `Nenhuma — contexto e gates claros`.
- Finalizar com: "ChatGPT, revise estes resultados e diga o próximo patch seguro; aguardarei orientação."
```

Se o agente não puder comentar pelo GitHub, **parar e mostrar o erro específico**, salvar a devolutiva em `docs/VALIDACAO_LOCAL_YYYYMMDD.md` numa branch de validação e pedir ao operador para colar o conteúdo na PR. **Não dizer que comentou se não houver link/ID confirmado**.

## 5. Fontes
- Print Generator: `App.tsx`, `app/bridge.py`, `soclick/client.py`, `soclick/discovery.py`, `soclick/render_receipt.py`, `render/engine.py`, `render/output.py`, `templates/*/template.json`, `tests/test_soclick_handoff.py`, `tests/test_render_receipt.py`.
- EvydFlow: `api/soclick_routes.py`, `soclick/print_intake.py`, `soclick/storage.py`, `soclick/models.py`, `soclick/runner.py`, `soclick/watchdog.py`, `api/static/soclick.js`, `api/production_routes.py`, `queue/runtime_pulse.py`, `services/start-evydflow.ps1`, `services/boot-evydflow.ps1`, `production/store.py`, `production/execution_plans.py`.
