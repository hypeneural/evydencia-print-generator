# Repository Map

Use este mapa para reduzir exploração e contexto desnecessários.

| Tarefa | Diretório principal | Leia antes |
|---|---|---|
| UX/React/Fabric | apps/ui/ | apps/ui/AGENTS.md, docs/UI_RUNTIME_ARCHITECTURE.md, docs/EDITOR_UX.md |
| Ingest/preview/renderer | apps/desktop/ | apps/desktop/AGENTS.md, docs/IMAGE_PIPELINE.md |
| Menu moderno Windows | native/windows-shell/ | native/windows-shell/AGENTS.md, docs/WINDOWS_CONTEXT_MENU_PRO.md |
| Instalador | installer/ | installer/AGENTS.md, docs/WINDOWS_CONTEXT_MENU_PRO.md |
| Produto/template | templates/ | templates/AGENTS.md, docs/PRODUCT_SPECS.md |
| Contratos | schemas/ | schemas/AGENTS.md, ADRs relacionados |
| Testes | tests/ | tests/AGENTS.md |
| Qualidade/gates | .github/, tests/, docs/ | docs/QUALITY_GATES.md |
| Customizações AntiGravity | .agents/ | docs/ANTIGRAVITY.md |
| CI/automação | .github/, scripts/ | docs/QUALITY_GATES.md, CONTRIBUTING.md |

## Dependências

```text
Windows shell -> desktop app / ingest
                     |
                     +-> SourceRegistry -> preview cache -> React/Fabric
                     |
                     +-> renderer Pillow <- Template + Job <- React/Fabric
```

## Exploração
1. Comece por esta tabela.
2. Leia o AGENTS.md mais próximo dos arquivos que serão alterados.
3. Leia ADRs somente quando a mudança toca a decisão correspondente.
4. Não abra todas as Skills; deixe a descrição ativar a Skill certa.
5. Feature transversal: /plan.
6. Auditoria: quality-auditor pode ampliar a busca depois do escopo inicial.
7. Antes de concluir qualquer tarefa, consulte docs/QUALITY_GATES.md.
