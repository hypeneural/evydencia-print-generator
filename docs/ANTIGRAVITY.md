# AntiGravity 2.19.1 — Operating Guide

Auditado em 2026-10-03 contra a documentação oficial.

## Baseline
O changelog oficial marca **v2.19.1 — 2026-09-30 — Latest**. A versão permite mensagens diretas a subagentes e corrige custom agents que ignoravam regras globais/de projeto.

Fontes:
- https://www.antigravity.google/docs/changelog
- https://www.antigravity.google/docs/rules/
- https://www.antigravity.google/docs/skills
- https://www.antigravity.google/docs/subagents
- https://www.antigravity.google/docs/slash-commands/
- https://www.antigravity.google/docs/hooks

## Estratégia de contexto
- `AGENTS.md`/GEMINI não usam frontmatter e são always-on.
- Rules modulares usam triggers e só guardam constraints/invariantes.
- Skills guardam procedimentos multi-etapa.
- Skills seguem progressive disclosure: name+description primeiro, corpo sob demanda.
- Skills complexas devem ter decision tree.
- Scripts/resources/examples ficam no bundle da skill.
- Scripts de skill devem ser usados como black box quando possível; rode `--help` antes de ler fonte grande.

## Slash commands do projeto
- `/plan`: feature transversal, refactor, contrato ou risco alto.
- `/grill-me`: UX/medidas/requisito ainda ambíguo.
- `/boost`: bugs difíceis de geometria/performance quando disponível.
- `/browser`: validar UI do Vite, fluxos e screenshots sintéticas.
- `/learn`: transformar correções recorrentes em Rule/Skill depois de revisar o diff.

## Agents

### Principal
`evydencia-builder`
Coordena vertical slices, contexto mínimo e gates.

### Subagentes
1. `product-architect` — Template/Job/geometria/ADR.
2. `editor-ux-engineer` — Operador/Gestor, fluxo e ergonomia.
3. `canvas-engineer` — React/Fabric/history/performance.
4. `render-engineer` — Pillow/EXIF/ICC/DPI/pixels.
5. `windows-engineer` — pywebview/shell/installer.
6. `quality-auditor` — auditor independente read-only na primeira passagem.

Pesquisa/benchmark pode paralelizar. Dois agentes não editam os mesmos arquivos simultaneamente.

## Skills
Workspace: `.agents/skills/<skill>/SKILL.md`.

Skills atuais:
- antigravity-maintenance
- editor-performance
- editor-ux
- fabric-canvas
- image-ingest-preview
- image-quality
- print-geometry
- product-onboarding
- render-golden-tests
- repo-audit
- template-authoring
- windows-shell-integration

## Hooks
`.agents/hooks.json` usa PostToolUse leve para validar customizações após escrita. O hook não deve virar um build global a cada arquivo.

## Workflows
Não criar novos workflows. Estão deprecated e serão retirados em 2026-11-01; usar Skills.

## Configuração
Configuração por projeto pertence a `/.gemini/config.json` quando necessária. Não criar arquivo vazio.

## Sequência recomendada no issue #4
1. `/plan M1 SourceRegistry + Preview Pipeline + Renderer do Calendário`
2. revisar artifact;
3. se surgirem decisões de interação/medida, `/grill-me`;
4. implementar E1/E2 em incrementos;
5. canvas-engineer + editor-ux-engineer implementam E3;
6. `/browser` contra Vite para validar UX;
7. quality-auditor roda auditoria independente;
8. CI verde + benchmark registrado.
