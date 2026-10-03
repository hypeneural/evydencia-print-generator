---
trigger: model_decision
description: "Aplica-se quando uma tarefa altera arquitetura, dependências principais, fronteiras UI/renderer/Windows, contratos Template/Job, persistência ou empacotamento."
---
# Architecture Decision Rules

- Priorize separação entre domínio, UI, render e integração do sistema operacional.
- Não criar engine específica por produto quando Template/Job puderem expressar a variação.
- Dependência nova precisa de justificativa, licença compatível, maturidade suficiente e impacto de bundle/installer documentado.
- Não acople contratos persistentes à serialização interna de Fabric.js, pywebview ou Pillow.
- Mudança incompatível exige ADR, versão de schema e estratégia de migração.
- Prefira uma fronteira pequena entre JavaScript e Python: comandos de domínio, não chamadas arbitrárias.
