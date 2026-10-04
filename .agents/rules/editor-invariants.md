---
trigger: model_decision
description: "Aplica-se a decisões de arquitetura, UX, estado ou performance do editor visual, incluindo Fabric.js, history, viewport, layers, ingest e modo Operador/Gestor."
---
# Editor Invariants

- Operador edita foto dentro de slots definidos; não recebe editor genérico de layers.
- Gestor edita estrutura/layers e publicação.
- Fabric usa preview; render usa original.
- Source decode/preview é deduplicado por source.
- Template/produção, PreviewLayout e Job são sistemas de coordenadas separados.
- Resize de janela nunca altera Job.
- Aspect ratio visual sempre preserva o canvas de produção.
- Cena Fabric persiste durante drag/wheel; não recarregar imagens nem limpar canvas no hot path.
- Continuous interaction produz uma entrada de history ao final.
- Overlay estrutural é protegido e não captura seleção.
- UI abre sem esperar preview; loading/error são estados normais.
- Geometria/render corretos não provam UX/preview corretos.
- Feature visual exige validação visual além de testes unitários.
