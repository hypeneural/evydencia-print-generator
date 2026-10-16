# Registro canônico de integração — Gerador + EvydFlow + SóClick
**Data do inventário:** 15/10/2026. **Estado:** trabalho testado parcialmente; NÃO implantado integralmente e NÃO aprovado para impressão física.
**Fonte:** verificações atuais de commits/PRs/ancestralidade no GitHub + [devolutiva do Antigravity PR #30](https://github.com/hypeneural/evydencia-print-generator/pull/30#issuecomment-6205087627). Medições e inspeções do Windows são *relatadas* pelo agente; o GitHub não confirma a execução física.

## PRs empilhadas: não fechar antes de integrar
| Camada | PR | Branch base → head | Estado |
|---|---|---|---|
| Gerador features anteriores absorvidas | [#20](https://github.com/hypeneural/evydencia-print-generator/pull/20), [#21](https://github.com/hypeneural/evydencia-print-generator/pull/21), [#22](https://github.com/hypeneural/evydencia-print-generator/pull/22), [#23](https://github.com/hypeneural/evydencia-print-generator/pull/23), [#24](https://github.com/hypeneural/evydencia-print-generator/pull/24) | HEADs ancestrais da #30 (`behind_by=0`) | **Fechadas sem merge** como absorvidas pela cadeia; commits e branches preservados |
| Gerador fundação SóClick | [#27](https://github.com/hypeneural/evydencia-print-generator/pull/27) | `feat/soclick-operator-handoff` → `codex/soclick-operational-readiness-20261015` | Draft; CI verde, não integrada |
| UX Chaveiro | [#28](https://github.com/hypeneural/evydencia-print-generator/pull/28) | #27 → `codex/keychain-multiselect-dblclick-ux-20261015` | Draft; CI verde, não integrada |
| Resiliência do handoff | [#29](https://github.com/hypeneural/evydencia-print-generator/pull/29) | #28 → `codex/print-generator-operational-recovery-20261015` | Draft; CI verde, não integrada |
| Pasta aprovada + auto-recuperação | [#30](https://github.com/hypeneural/evydencia-print-generator/pull/30) | #29 → `codex/soclick-unified-handoff-recovery-20261015` | Draft; HEAD `acbaabee`, CI verde, ainda sem canário DRAFT |
| EvydFlow release consolidado | [#37](https://github.com/hypeneural/evydflow/pull/37) | `main` → `fix/p0-soclick-copy-order-crm-links-timeline-20261013` | Draft; cabeça `bd47a4c0`; ~803 commits sobre main, release ampla, **alto risco de merge cego** |
| EvydFlow boot/pasta | [#42](https://github.com/hypeneural/evydflow/pull/42) | #37 → `codex/soclick-approved-staging-boot-20261015` | Draft; HEAD `43426b25` ou posterior, sem aprovação de restart |
| EvydFlow status legado | [#39](https://github.com/hypeneural/evydflow/pull/39) | Ramificação antiga da #37 | **Fechada sem merge como superseded**: script/doc já na #37, único teste novo portado à #42 no commit `43426b25` (blobs idênticos) |
| EvydFlow branches anteriores absorvidas | [#32](https://github.com/hypeneural/evydflow/pull/32), [#33](https://github.com/hypeneural/evydflow/pull/33), [#35](https://github.com/hypeneural/evydflow/pull/35), [#36](https://github.com/hypeneural/evydflow/pull/36) | HEAD de cada uma é ancestral da #37 (`behind_by=0`) | **Fechadas sem merge** como absorvidas, com comentários e branches históricas preservadas |
| EvydFlow patches históricos | [#40](https://github.com/hypeneural/evydflow/pull/40), [#41](https://github.com/hypeneural/evydflow/pull/41) | Base #37 | Já **merged** na base #37; preservar histórico, não reabrir |

**Ancestralidade confirmada:** `print-generator/main` é ancestral do head #30, mas ainda há aproximadamente **123 commits** não integrados, incluindo a fundação anterior à #27. `evydflow/main` é ancestral do head #37, que contém aproximadamente **803 commits** ainda não presentes na main. CI de PR #30 não é CI de toda a árvore EvydFlow. `merged` de #40/#41 significa merge na **branch de base**, não necessariamente publicação em main.

## Auditoria da devolutiva Antigravity: confiança/limites
**Evidência positiva relatada:** Windows 11 Home / PowerShell 5.1; 307 testes Vitest; 41 Python PASS + 1 SKIP; 39 testes EvydFlow; AST PowerShell sem erros; DRY RUN sem alterar `pilot-context.env`; pywebview 1024x680 responsivo; staging por hash/bytes para Calendário (1067x1474 @254 DPI) e Chaveiro (2551x1795 @300 DPI). `API 8095` e worker foram mantidos ativos. A sessão real NÃO executou `-Apply`, restart nem DRAFT.

**Pendência técnica P0:** `recover-api.ps1` do Antigravity está **somente em seu scratch local e colado no comentário**, não em `services/` da PR #42. Foi validado por parser AST e harness isolado, **não** contra API/worker reais. Antes de integrar, deve ser versionado, revisado e testado (atualização de ledger sob mutex, riscos de PID reutilizado, pré-validação de segredos antes de parar serviço, parada graciosa ao invés de `Stop-Process -Force`, rollback do processo + configuração, invariantes worker/API e dado em SQLite). `services/boot-evydflow.ps1` na PR #42 já tem guarda fail-closed para evitar segundo worker após queda isolada de API; botão `Reativar painel` pode recusar neste cenário e NÃO deve ser vendido como auto-recuperação 100%.

**Atenção ao banco:** o relatório indica `soclick_jobs.db`: 3 CREATED, 1 READY_FOR_PRODUCTION e 1 CANCELLED; `production_outbox`: 0; persist-queue com 21 `ack_failed` históricos. Isso **não prova** ausência universal de eventos pendentes; classificar eventos ack_failed/reprocessamento e quaisquer pedidos autorizados ANTES de reiniciar. Só clicar `Reativar` não autoriza upload físico.

**Performance:** p50/p95 com apenas cinco renders por produto são amostras preliminares; `requestAnimationFrame` próximo de 6 ms em monitor 165 Hz não prova consistência de 165 FPS sob operação pesada. Medir frame drops e p95/p99 em gestos reais, memória da árvore pywebview e render frio/quente. O screenshot/artefatos locais `file:///C:/...` não são arquivos auditáveis via GitHub.

## Checklist para encerramento técnico
- [x] CI da #30 verde no HEAD `acbaabee`, testes de isolamento WebView2 e estabilidade JPEG.
- [x] PRs do Gerador #20–#24 encerradas como absorvidas pela cadeia #30, e PRs EvydFlow #32/#33/#35/#36 absorvidas pela #37. PR #39 fechada após portar o único teste exclusivo para #42. Tudo sem merge adicional nem exclusão de branches.
- [ ] Inserir e auditar supervisor `recover-api.ps1` em #42; testes P0 de recuperação API-only sem duplicar workers.
- [ ] Validar CI completo atual da release EvydFlow #37 + #42 e migrações/schema no banco canônico.
- [ ] Conferir ACL/backup da pasta segura, planejar `-Apply` e restart API com aprovações **separadas**.
- [ ] No Windows 11 Home real, executar canário **exclusivamente DRAFT sintético** no SQLite `EVYDFLOW_SOCLICK_DB_PATH`; verificar SHA e link do editor sem `/submit` nem envio físico.
- [ ] Homologar rollback e reabertura do app, comportamento offline, UX/legibilidade, recuperação de crash.
- [ ] Resolver retenção/limpeza dos JPEGs staged sem excluir DRAFT referenciado.
- [ ] Após homologação e revisão dos limites, integrar as PRs **em ordem topológica**, revalidando a árvore de destino e a main em cada etapa; nunca presumir que fechar Draft é merge.
- [ ] Só depois excluir branches *merged* e comprovadamente sem worktrees/checkouts ativos; **não** apagar histórico de PRs fechadas. Sem API conectada para excluir refs, deixar para operação GitHub controlada.

## Política AI-first para organização
- Atualizar as PRs existentes, sem novas PRs de testes nem novas branches temporárias persistentes.
- Um comentário de fechamento por gate com SHA, comandos PASS/FAIL/NOT_RUN, changelog, links de logs/screenshot e decisão GO/NO-GO.
- Não fechar PRs #27–#30 nem #37/#42 enquanto suas mudanças não estiverem integradas à base final. Para PRs antigas fora desta cadeia: inventariar ancestralidade e fazer uma revisão separada de *absorvida vs divergente* antes de encerrar.
- Nenhum merge automático, reset agressivo, parada/restart em produção ou exclusão de branches baseada apenas em CI.
