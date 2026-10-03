---
trigger: glob
description: "Valida estrutura e compatibilidade das customizações AntiGravity ao editar AGENTS, rules, skills, agents ou hooks."
globs: "AGENTS.md, **/AGENTS.md, .agents/**/*.md, .agents/hooks.json"
---
# Antigravity Customization Rules

- AGENTS.md não usa frontmatter e deve permanecer enxuto.
- Rules em .agents/rules são arquivos .md planos com frontmatter e trigger válido: always_on, model_decision, glob ou manual.
- Skills ficam em .agents/skills/<name>/SKILL.md; descrição deve dizer o que faz e quando usar.
- Prefira scripts/resources/examples dentro da própria skill em vez de aumentar SKILL.md.
- Workflows legados não devem ser criados; use Skills.
- Custom agents ficam em .agents/agents/<name>/agent.md e devem declarar name/description/mainAgent/subagent/model/commandExecutionPolicy.
- Se declarar tools, use somente nomes documentados; nome inválido pode travar o subagente.
- Regras invariantes vão em Rule/AGENTS; procedimentos multi-etapa vão em Skill.
- Após editar customizações, rode: python scripts/verify_antigravity_customizations.py
