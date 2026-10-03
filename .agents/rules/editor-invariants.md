---
trigger: model_decision
description: "Aplica-se a decisões de arquitetura, UX, estado ou performance do editor visual, incluindo Fabric.js, history, layers, ingest e modo Operador/Gestor."
---
# Editor Invariants

- Operador não recebe um editor genérico de layers; ele edita a foto dentro de slots definidos.
- Gestor pode editar estrutura/layers, mas publicação exige validação.
- Original full-resolution não deve ficar no runtime Fabric no fluxo comum.
- Preview/proxy é descartável; render usa original.
- Source decode/preview deve ser deduplicado por source.
- Continuous interactions não gravam dezenas de history entries.
- z-order estrutural pertence ao Template, não ao Job do Operador.
- UI deve permanecer útil enquanto preview/render rodam em background.
- Recursos novos precisam declarar impacto no tempo de abertura, interação e memória.
