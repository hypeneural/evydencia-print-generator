---
name: antigravity-maintenance
description: Audita e atualiza AGENTS.md, rules, skills, hooks e custom agents contra a documentação/changelog oficial do Google Antigravity. Use em upgrades do AntiGravity, falhas de descoberta de customizações ou otimização de contexto/performance.
---
# Antigravity Maintenance

1. Confirme a versão alvo no changelog oficial antes de alterar a estrutura.
2. Revise Rules, Skills, Custom Subagents, Hooks e migrations oficiais relevantes.
3. Compare o repositório com a versão anterior e identifique customizações redundantes/obsoletas.
4. Prefira progressive disclosure: root AGENTS curto; AGENTS por diretório; Rules condicionais; Skills focadas.
5. Não recrie capacidade nativa: use /plan em vez de uma skill local de planejamento.
6. Valide com `python scripts/verify_antigravity_customizations.py`.
7. Registre mudanças significativas em `docs/audits/` e STATUS.md.

## Fontes oficiais
- https://www.antigravity.google/docs/changelog
- https://www.antigravity.google/docs/rules/
- https://www.antigravity.google/docs/skills
- https://www.antigravity.google/docs/subagents
- https://www.antigravity.google/docs/hooks
- https://www.antigravity.google/docs/migration/workflows-to-skills
