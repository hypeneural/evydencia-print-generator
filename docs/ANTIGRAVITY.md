# AntiGravity 2.19.1 — Repository Operating Guide

Auditado em 2026-10-03 contra a documentação oficial.

## Versão
Antigravity 2.19.1 é a versão mais recente da linha Antigravity 2.0 no changelog oficial em 2026-09-30. A versão corrige custom agents que ignoravam regras globais/de projeto e permite enviar mensagens diretamente a subagentes.

Fonte: https://www.antigravity.google/docs/changelog

## Regras
- AGENTS.md/GEMINI.md não usam frontmatter e são always-on no escopo do diretório.
- Rules em .agents/rules/*.md precisam de trigger válido.
- Regras são cumulativas; diretório mais específico tem precedência.
- Regras expressam invariantes; Skills expressam procedimentos.

Fonte: https://www.antigravity.google/docs/rules/

## Skills
Skills ficam em .agents/skills/<skill>/SKILL.md. Só name/description entram inicialmente no contexto; corpo e recursos são carregados sob demanda. Scripts/examples/resources devem ficar dentro da skill quando específicos.

Fonte: https://www.antigravity.google/docs/skills

## Workflows e planejamento
Workflows estão deprecated e serão retirados em 2026-11-01. Não criar workflows novos. Desde 2.17, /plan oferece exploração sem efeitos colaterais, artifact review e Proceed; por isso este projeto não mantém uma skill duplicada de planning.

Fontes:
- https://www.antigravity.google/docs/migration/workflows-to-skills
- https://www.antigravity.google/docs/plan/

## Custom agents
Local: .agents/agents/<name>/agent.md.
O projeto usa allowlists de tools documentadas, model/policy explícitos e skills por agente. O coordenador declara dependências dos especialistas.

Fonte: https://www.antigravity.google/docs/subagents

### Estratégia
- evydencia-builder: principal/orquestrador.
- product-architect: contratos/geometria.
- canvas-engineer: React/Fabric.
- render-engineer: Pillow/bitmap.
- windows-engineer: shell/installer.
- quality-auditor: revisão independente somente leitura.

Não paralelizar agentes que editam os mesmos arquivos.

## Hooks
Workspace hooks ficam em .agents/hooks.json. O hook deste repo roda somente após ferramentas de escrita e só efetivamente valida quando a escrita toca customizações.

Fonte: https://www.antigravity.google/docs/hooks

## Configuração de projeto
Desde 2.17, customização por repositório usa /.gemini/config.json; .agents/settings.json não é mais lido. Não criar config vazio: só usar quando houver configuração real.

## Verificação manual após clone
1. Customizations → confirme Rules/Skills/Hooks.
2. /agents → confirme os seis agentes.
3. /plan → valide artifact review numa mudança pequena.
4. Rode python scripts/verify_antigravity_customizations.py.
