---
trigger: model_decision
description: "Aplica-se quando o agente declara tarefa, PR, milestone, UI, CI, Windows, performance ou produção como pronta, concluída, validada ou 100%."
---
# Completion Evidence

Antes de declarar conclusão:
1. identifique o SHA exato;
2. diferencie testes locais de CI remoto;
3. se houver branch/PR remoto, consulte o último run remoto;
4. UI/layout exige evidência visual;
5. performance exige medição;
6. Windows UI exige validação em Windows real;
7. impressão/cor exige gate físico quando aplicável.

Não transformar evidência indireta em prova:
- output correto != preview correto;
- package registrado != menu visível;
- pytest local != Actions verde.

Use vocabulário de docs/QUALITY_GATES.md e registre risco residual.
