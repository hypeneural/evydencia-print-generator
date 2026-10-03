---
trigger: model_decision
description: "Use ao adicionar, remover, atualizar ou trocar bibliotecas Python/Node, bundlers, empacotadores ou frameworks."
---
# Dependency Policy

Antes de alterar dependências:
1. valide a versão estável atual e documentação oficial;
2. confirme licença e riscos de distribuição desktop;
3. verifique manutenção recente e advisories relevantes;
4. explique por que biblioteca existente não resolve o requisito;
5. prefira dependências diretas pequenas em vez de forks grandes;
6. atualize `docs/UPSTREAM_REFERENCES.md` quando a decisão arquitetural mudar.

Não faça upgrade amplo junto com feature funcional sem necessidade.
