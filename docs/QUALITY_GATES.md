# Quality Gates

Este documento define o que "pronto" significa. Evidência deve provar o contrato relevante; uma classe de teste não substitui outra.

## Regra central
**Não inferir conclusão a partir de evidência indireta.**

Exemplos:
- JPEG final correto não prova preview correto.
- pytest local verde não prova GitHub Actions verde.
- package registrado não prova comando visível no Explorer.
- screenshot bonita não prova render físico correto.

## Gates

### G1 — Repository
- working tree/branch/SHA identificados;
- sem segredo/foto real/path pessoal novo;
- verify_repo e lints relevantes passam.

### G2 — Unit/Contract
- testes da área alterada passam;
- contratos Template/Job permanecem determinísticos;
- mudanças de schema têm migration/ADR quando necessário.

### G3 — Remote CI
Quando existe branch/PR remoto:
- consultar o run remoto após o último SHA;
- todos os jobs obrigatórios devem estar SUCCESS;
- "local green" deve ser reportado separadamente de "remote green".

### G4 — UI/Visual
Obrigatório para layout/interação:
- proporção visual validada;
- 1024×680, 1280×800 e 1920×1080 quando aplicável;
- switch entre produtos sem drift;
- screenshot/inspeção com fixture sintética;
- /browser ou teste E2E visual quando útil.

### G5 — Performance
Mudança no hot path exige:
- cenário e máquina registrados;
- antes/depois;
- nenhuma nova decode/reload/alocação pesada em pointermove/wheel;
- orçamento de docs/PERFORMANCE_BUDGETS.md respeitado ou risco aceito explicitamente.

### G6 — Windows
Integração Shell só é validada quando:
- contrato nativo passa;
- package/identity/trust estão corretos;
- comando é visto no menu moderno de um Windows real;
- Invoke funciona;
- uninstall/lifecycle foram verificados quando escopo da entrega.

### G7 — Produção física
Quando a mudança altera geometria/cor/qualidade:
- dimensões e DPI validados;
- política ICC/JPEG explícita;
- prova física quando necessária.

## Vocabulário permitido
- PASS local
- PASS CI remoto
- VISUAL PASS
- MANUAL WINDOWS PASS
- PHYSICAL PASS
- BLOCKED
- READY_FOR_HUMAN_MERGE
- READY_FOR_NEXT_PHASE

Evite "100% validado" sem listar quais gates passaram.

## Merge
Não empurrar diretamente para main em mudança não trivial. Preferir branch + PR + checks.
