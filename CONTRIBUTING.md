# Contributing

1. Leia AGENTS.md da raiz e da área alterada.
2. Para feature não trivial use /implementation-plan.
3. Branch curta por assunto; não misture upgrade amplo com feature.
4. Testes na mesma mudança.
5. UI: screenshots apenas com fixture sintética.
6. Template/schema: rode python scripts/validate_templates.py.
7. Antes do PR: python scripts/verify_repo.py + pytest + lints.
8. Não inclua fotos reais, caminhos de produção, credentials ou outputs.
9. PR informa escopo, critérios de aceite, testes, riscos e migração de schema/template.
