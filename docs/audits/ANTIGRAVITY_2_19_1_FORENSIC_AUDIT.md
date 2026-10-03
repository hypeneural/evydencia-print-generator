# Auditoria Forense — AntiGravity 2.19.1

**Data:** 2026-10-03  
**Repositório:** `hypeneural/evydencia-print-generator`  
**Versão alvo:** AntiGravity 2.19.1  
**Gate final:** `READY_FOR_NEXT_PHASE`

## Fontes oficiais validadas
- Changelog: https://www.antigravity.google/docs/changelog
- Rules: https://www.antigravity.google/docs/rules/
- Skills: https://www.antigravity.google/docs/skills
- Custom subagents: https://www.antigravity.google/docs/subagents
- Hooks: https://www.antigravity.google/docs/hooks
- Plan: https://www.antigravity.google/docs/plan/
- Workflow migration: https://www.antigravity.google/docs/migration/workflows-to-skills

## Baseline oficial
O changelog oficial marca **v2.19.1 (2026-09-30)** como Latest. A release adiciona mensagens diretas para subagentes e corrige custom agents que ignoravam regras globais/de projeto.

Rules:
- `AGENTS.md`/`GEMINI.md` não usam frontmatter e são always-on no escopo.
- `.agents/rules/*.md` exige trigger válido.
- `model_decision` e Skills permitem progressive disclosure.

Skills:
- workspace: `.agents/skills/<name>/SKILL.md`;
- metadata é indexada antes do corpo;
- scripts/resources/examples podem ser agrupados no bundle.

Subagents:
- workspace: `.agents/agents/<name>/agent.md` ou arquivo .md direto;
- frontmatter suporta tools, mainAgent, subagent, model, commandExecutionPolicy e skills;
- `agents` permite declarar subagentes dependentes;
- tool names inválidos são risco conhecido de hang.

Hooks:
- workspace: `.agents/hooks.json`;
- `PostToolUse` recebe toolCall + args e retorna `{}`.

Workflows:
- deprecated;
- retirada anunciada para 2026-11-01;
- Skills substituem workflows com carregamento progressivo.

## Achados e correções

### A-01 — protocolo local de planejamento duplicava /plan — HIGH — RESOLVIDO
A skill `implementation-plan` duplicava capacidade nativa. Removida. O root agora orienta `/plan`, que explora sem escrever, cria artifact revisável e só executa após Proceed.

### A-02 — ausência de agente principal de domínio — HIGH — RESOLVIDO
Criado `evydencia-builder`, mainAgent responsável por coordenação e delegação.

### A-03 — toolsets de agentes implícitos/subespecificados — MEDIUM — RESOLVIDO
Todos os agentes declaram toolsets usando nomes oficiais. `quality-auditor` não recebe ferramentas explícitas de escrita.

### A-04 — ausência de validação automática de customizações — MEDIUM — RESOLVIDO
Adicionado `.agents/hooks.json` com PostToolUse leve e `verify_antigravity_customizations.py`.

### A-05 — CI referenciava scripts inexistentes — BLOCKER — RESOLVIDO
Publicados:
- `verify_antigravity_customizations.py`
- `validate_templates.py`
- `check_privacy.py`
- `verify_repo.py`

### A-06 — documentação AntiGravity insuficiente — MEDIUM — RESOLVIDO
Adicionados `docs/ANTIGRAVITY.md` e este relatório.

### A-07 — decisões arquiteturais sem ADR físico — MEDIUM — RESOLVIDO
Materializados ADR-001..ADR-007 e `verify_repo.py` agora exige sua presença.

### A-08 — GitHub Actions legado e warnings Node 20 — MEDIUM — RESOLVIDO
Atualizado para `actions/checkout@v7` + `actions/setup-python@v7`, conforme documentação/release atual.

### A-09 — lint bloqueando CI — LOW — RESOLVIDO
Corrigidos imports e formatação detectados pelo Ruff.

### A-10 — repositório público — NOTE — ABERTO
A API do GitHub reporta `visibility=public`. Nenhuma fotografia real, segredo ou caminho privado pode entrar. Se o código precisar ser privado, alterar a visibilidade no GitHub.

## Organização final das customizações

```text
AGENTS.md
├── apps/ui/AGENTS.md
├── apps/desktop/AGENTS.md
├── templates/AGENTS.md
├── schemas/AGENTS.md
├── installer/AGENTS.md
└── tests/AGENTS.md

.agents/
├── agents/
│   ├── evydencia-builder/
│   ├── product-architect/
│   ├── canvas-engineer/
│   ├── render-engineer/
│   ├── windows-engineer/
│   └── quality-auditor/
├── rules/
│   ├── architecture.md
│   ├── dependency-policy.md
│   ├── privacy.md
│   └── customizations.md
├── skills/
│   ├── antigravity-maintenance/
│   ├── fabric-canvas/
│   ├── print-geometry/
│   ├── product-onboarding/
│   ├── render-golden-tests/
│   ├── repo-audit/
│   ├── template-authoring/
│   └── windows-shell-integration/
└── hooks.json
```

## Por que isso é performático
1. O root always-on contém somente invariantes.
2. Detalhes de UI/Python/Templates/Windows são carregados por diretório.
3. Rules condicionais não despejam todo o conteúdo em cada turno.
4. Skills carregam metadata primeiro e corpo apenas sob demanda.
5. O agente principal coordena; especialistas têm contexto menor e toolsets focados.
6. O quality-auditor atua separadamente para reduzir auto-validação enviesada.
7. `/plan` nativo substitui prompt de planejamento duplicado.
8. Hook roda o verificador apenas quando uma escrita toca customizações.

## Evidência mecânica
### Run anterior
Run #11 encontrou quatro problemas de lint após todo o restante passar:
- validators: OK;
- 3 templates: OK;
- privacy: OK;
- pytest: 2 passed;
- Ruff: 4 findings.

### Run final
**GitHub Actions #16 — SUCCESS**
- SHA: `b7bc07873497a01d6f10e074d1323646d9ed24bc`
- Ubuntu/contracts: SUCCESS
- Windows/windows-contract: SUCCESS
- `verify_repo.py`: SUCCESS
- `pytest -q`: SUCCESS
- `ruff check`: SUCCESS
- Windows CLI/bootstrap contract: SUCCESS

https://github.com/hypeneural/evydencia-print-generator/actions/runs/37152264949

## Conclusão
A configuração AntiGravity não é mais o bloqueio do projeto. O repositório está pronto para entrar na Fase 1/2: fechar geometria física pendente e implementar o renderer determinístico.
