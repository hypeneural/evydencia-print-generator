# AntiGravity — Operating Guide

Auditado em 2026-10-04 contra documentação oficial.

## Versão alvo
A página oficial de download lista **Antigravity 2.0 v2.19.1** para Windows/macOS/Linux.

Importante: o changelog público consultado em 2026-10-04 ainda marca **v2.18.1** como Latest. Portanto, este repositório não atribui mudanças específicas à v2.19.1 sem release notes oficiais correspondentes.

Fontes oficiais:
- https://www.antigravity.google/download
- https://www.antigravity.google/docs/changelog
- https://www.antigravity.google/docs/rules/
- https://www.antigravity.google/docs/skills
- https://www.antigravity.google/docs/subagents
- https://www.antigravity.google/docs/slash-commands/
- https://www.antigravity.google/docs/artifact-review
- https://www.antigravity.google/docs/hooks
- https://www.antigravity.google/docs/migration/workflows-to-skills

## Contexto e Rules
- AGENTS.md/GEMINI.md não usam frontmatter e ficam always-on no escopo do diretório.
- Rules em .agents/rules/*.md precisam de frontmatter válido e trigger documentado.
- Rules são cumulativas; regra mais específica de diretório prevalece em conflito.
- Rules aninhadas em subpastas não são descobertas automaticamente sem registro explícito.
- Root AGENTS deve conter apenas invariantes estáveis e roteamento de contexto.

## Skills
- Skills ficam em .agents/skills/<name>/SKILL.md.
- Antigravity indexa name + description e carrega o corpo sob demanda.
- Uma Skill deve resolver uma responsabilidade específica.
- Skills complexas devem conter decision tree.
- Scripts/resources/examples devem ficar no bundle da Skill para evitar prompt bloat.
- Quando uma Skill oferecer script auxiliar, prefira executar --help/uso documentado antes de ler implementação inteira.

## Subagentes
- Custom agents ficam em .agents/agents/<name>/agent.md ou .agents/agents/<name>.md.
- Subagentes iniciam com contexto isolado da conversa do pai.
- Para paralelismo com escrita, prefira workspace isolado/worktree (branch) por subagente.
- Pesquisa e auditoria podem paralelizar; dois agentes não editam o mesmo arquivo ao mesmo tempo.
- Nome de tool inválido pode travar um subagente; mantenha validação mecânica.

## Planejamento e revisão
Política recomendada neste projeto: **Request Review**.

- /plan: mudanças multi-arquivo, arquitetura, contratos ou risco alto.
- /grill-me: requisito de UX/produto ainda ambíguo.
- /boost: bugs/algoritmos/performance difíceis quando disponível.
- /browser: inspeção de UI real e navegação.
- /learn: transformar correções recorrentes em Rule/Skill após revisar o diff.
- /teamwork-preview: migrações ou campanhas repo-scale; não usar como padrão para feature localizada.
- /goal: só quando execução autônoma contínua for realmente desejada; não usar em mudanças que exigem gates humanos.
- /btw: pergunta lateral sem interromper o fluxo principal.

Um Implementation Plan não é aprovação de código. O agente deve parar para review quando o gate exigir validação humana ou visual.

## Hooks
Hooks devem ser rápidos e específicos. O projeto usa PostToolUse para validar customizações; não transformar hook em build global a cada edição.

## Workflows
Workflows legados serão retirados em **2026-11-01**. Não criar novos workflows; use Agent Skills.

## Política de conclusão
Nunca declarar "100%", "concluído", "validado" ou "produção" apenas porque testes locais passaram.
Aplique docs/QUALITY_GATES.md e diferencie:
- unit/contract evidence;
- CI remoto;
- visual/UI evidence;
- Windows/manual evidence;
- impressão física quando aplicável.
