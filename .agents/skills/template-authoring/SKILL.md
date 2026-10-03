---
name: template-authoring
description: Cria ou revisa templates data-driven de impressão, slots, grupos, overlays, permissões e versionamento. Use ao mudar qualquer produto físico ou modo Gestor.
---
# Template Authoring

1. Leia `docs/PRODUCT_SPECS.md` e `templates/AGENTS.md`.
2. Separe fatos confirmados de valores derivados/TBD.
3. Use mm para canvas/slots/gaps/margens.
4. Defina slots, grupos e overlays explicitamente.
5. Marque `draft` enquanto houver coordenada/medida pendente.
6. Não salve JSON interno do Fabric como template de domínio.
7. Rode `python scripts/validate_templates.py`.
8. Se mudar contrato: schema + ADR + migração + testes.
9. Só promova para `production` após prova física registrada.
