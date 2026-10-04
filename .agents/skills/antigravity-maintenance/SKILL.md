---
name: antigravity-maintenance
description: Audita e atualiza AGENTS.md, rules, skills, hooks e custom agents contra a documentação oficial do Google Antigravity. Use em upgrades ou otimização de contexto.
---
# Antigravity Maintenance

1. Confirme versão distribuída na página oficial de download.
2. Consulte também changelog; se houver divergência entre download/changelog, registre-a e não invente release notes.
3. Revise Rules, Skills, Subagents, Hooks, Slash Commands e Artifact Review.
4. Root AGENTS: só invariantes/roteamento.
5. Rules: constraints persistentes; Skills: procedimentos.
6. Skills focadas + progressive disclosure + resources/scripts.
7. Em escrita paralela de subagentes, prefira worktree/branch isolado.
8. Não recrie capacidade nativa: /plan, /grill-me, /browser, /boost e /teamwork-preview quando apropriados.
9. Request Review é o padrão para mudanças de arquitetura/alto risco.
10. Rode `python scripts/verify_antigravity_customizations.py`.
11. Atualize auditoria/status sem declarar capacidades não comprovadas.

## Fontes
- https://www.antigravity.google/download
- https://www.antigravity.google/docs/changelog
- https://www.antigravity.google/docs/rules/
- https://www.antigravity.google/docs/skills
- https://www.antigravity.google/docs/subagents
- https://www.antigravity.google/docs/slash-commands/
- https://www.antigravity.google/docs/artifact-review
- https://www.antigravity.google/docs/hooks
- https://www.antigravity.google/docs/migration/workflows-to-skills
