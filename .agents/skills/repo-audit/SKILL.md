---
name: repo-audit
description: Audita o repositório antes de merge/release ou após mudanças grandes, cobrindo arquitetura, contratos, testes, CI, privacidade, dependências e integração Windows. Use para revisão forense e gate de qualidade.
---
# Repository Audit

## Procedimento
1. Registre branch/SHA e estado do working tree.
2. Leia `AGENTS.md` da raiz e das áreas tocadas.
3. Compare mudanças com `PLAN.md`, `STATUS.md`, ADRs e specs.
4. Rode `python scripts/verify_repo.py`.
5. Rode testes/lints adicionais da área alterada.
6. Para UI, valide estado/serialização, resize e screenshots com fixture sintética.
7. Para render, execute golden tests e confira dimensões físicas/pixels.
8. Para Windows, valide comando, quoting, instalação/desinstalação e matriz Win10/11 quando disponível.
9. Verifique dependências/licenças e que não entrou dado privado.
10. Classifique achados: BLOCKER / HIGH / MEDIUM / LOW / NOTE.

## Saída
- Evidence/commands
- Findings por severidade
- Riscos residuais
- Próximo passo objetivo
- Gate: `BLOCKED`, `READY_FOR_NEXT_PHASE` ou `READY_FOR_HUMAN_MERGE`
