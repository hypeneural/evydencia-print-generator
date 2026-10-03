# Repository Map

Este arquivo existe para reduzir exploração desnecessária do AntiGravity.

## Onde editar

| Tarefa | Diretório principal | Leia antes |
|---|---|---|
| UX/React/Fabric | `apps/ui/` | `apps/ui/AGENTS.md`, `docs/EDITOR_UX.md` |
| Ingest/preview/renderer | `apps/desktop/` | `apps/desktop/AGENTS.md`, `docs/IMAGE_PIPELINE.md` |
| Menu moderno Windows | `native/windows-shell/` | `native/windows-shell/AGENTS.md`, `docs/WINDOWS_CONTEXT_MENU_PRO.md` |
| Instalador | `installer/` | `installer/AGENTS.md`, `docs/WINDOWS_CONTEXT_MENU_PRO.md` |
| Produto/template | `templates/` | `templates/AGENTS.md`, `docs/PRODUCT_SPECS.md` |
| Contratos | `schemas/` | `schemas/AGENTS.md`, ADRs |
| Testes | `tests/` | `tests/AGENTS.md` |
| Customizações AntiGravity | `.agents/` | `docs/ANTIGRAVITY.md` |
| CI/automação repo | `.github/`, `scripts/` | `CONTRIBUTING.md` |

## Dependências arquiteturais

```text
Windows shell
    │
    ▼
desktop app / ingest
    │
    ├── SourceRegistry ──► preview cache ──► React/Fabric
    │
    └── renderer Pillow ◄── Template + Job
                              ▲
                              │
                         React/Fabric
```

## Regras de exploração

1. Comece pelo arquivo desta tabela; não faça varredura recursiva do repo por padrão.
2. Leia o `AGENTS.md` mais próximo do arquivo que será alterado.
3. Só leia ADRs relacionados à mudança.
4. Não leia todas as Skills; o AntiGravity deve carregar a skill relevante sob demanda.
5. Para feature transversal, use `/plan` e limite o escopo a módulos explícitos.
6. Para auditoria, `quality-auditor` pode ampliar a busca depois que o escopo inicial estiver definido.
