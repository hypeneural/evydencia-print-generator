---
name: repo-audit
description: Audita o repositório antes de merge/release ou após mudanças grandes, cobrindo arquitetura, contratos, testes, CI remoto, UI visual, privacidade e Windows.
---
# Repository Audit

1. Registre branch/SHA/working tree.
2. Leia AGENTS da raiz e áreas tocadas.
3. Compare com STATUS/PLAN/ADRs/specs.
4. Rode verify_repo + testes/lints da área.
5. Se há branch/PR remoto, consulte Actions do último SHA.
6. Para UI, use /ui-visual-validation; não inferir UI por renderer.
7. Para render, golden/dimensões/DPI.
8. Para Windows, separar contract/package/trust de UI manual.
9. Verifique privacidade/dependências.
10. Classifique BLOCKER/HIGH/MEDIUM/LOW/NOTE.

## Gate
Use docs/QUALITY_GATES.md.
Saída: evidências, riscos e `BLOCKED`, `READY_FOR_NEXT_PHASE` ou `READY_FOR_HUMAN_MERGE`.
