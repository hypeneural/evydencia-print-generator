# Auditoria Forense — AntiGravity 2.19.1

Data: 2026-10-03
Escopo: hypeneural/evydencia-print-generator

## Fontes oficiais
- https://www.antigravity.google/docs/changelog
- https://www.antigravity.google/docs/rules/
- https://www.antigravity.google/docs/skills
- https://www.antigravity.google/docs/subagents
- https://www.antigravity.google/docs/hooks
- https://www.antigravity.google/docs/plan/
- https://www.antigravity.google/docs/migration/workflows-to-skills

## Achados

### A-01 — planning local duplicava /plan nativo — HIGH
Desde v2.17 existe /plan com exploração sem side effects, Implementation Plan revisável e Proceed. A skill local implementation-plan deve ser removida.

### A-02 — faltava agente principal de domínio — HIGH
Só existiam especialistas subagent-only. Criado evydencia-builder para coordenação explícita.

### A-03 — toolsets dos subagentes não estavam explícitos — MEDIUM
A especificação aceita allowlists e alerta que tool name inválido pode travar execução. Foram usados apenas nomes documentados. quality-auditor não recebe tools de escrita.

### A-04 — faltava hook de sanidade — MEDIUM
Rule inválida pode ser descartada silenciosamente. Criado PostToolUse focado em customizações.

### A-05 — CI referencia scripts inexistentes — BLOCKER
O bootstrap inicial apontava para verificadores ainda não publicados. O commit seguinte deve publicar os validadores e contratos antes de considerar o bootstrap verde.

### A-06 — documentação local de versão inexistente — MEDIUM
Criado docs/ANTIGRAVITY.md para evitar pesquisas repetidas e convenções antigas.

### A-07 — repositório público — NOTE
A API do GitHub reporta visibility=public. Nenhuma foto/segredo pode entrar no repo; se o código também precisar ser privado, alterar visibility nas configurações do GitHub.

## 2.19.1 aproveitado
- custom agents voltam a respeitar rules;
- mensagens diretas para subagentes;
- root rules não precisam carregar processos multi-etapa graças a Skills;
- /plan substitui protocolo local de planejamento.

## Gate
Customização: READY após validação automática.
Produto: permanece em Fase 1.
