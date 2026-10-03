# EVYDÊNCIA Print Generator

Aplicativo desktop Windows local para compor produtos fotográficos de impressão da EVYDÊNCIA por templates e slots de foto, com fluxo simples para o operador e configuração controlada para o gestor.

## Fluxo alvo

1. Botão direito sobre uma foto no Windows → **Gerar com EVYDÊNCIA**.
2. Escolher produto: Calendário, Chaveiro ou Globo.
3. Ajustar cada foto com arrastar, zoom e rotação dentro do slot.
4. Gerar arquivo final sem alterar a fotografia original.

Também deve funcionar aberto diretamente, sem menu de contexto.

## Produtos iniciais

| Produto | Canvas físico | Slots | Estado |
|---|---:|---:|---|
| Chaveiro 3x4 | 216 × 152 mm | 18 (6×3), 34 × 44 mm | geometria conhecida; pareamento precisa prova física |
| Calendário 2027 | dimensão física a confirmar | 1 | overlay PNG recebido; pan/zoom/rotação |
| Globo de neve | 152 × 102 mm | 2 × 50 × 80 mm | posições X/Y pendentes |

Veja `docs/PRODUCT_SPECS.md`.

## Arquitetura

- **React + TypeScript + Fabric.js 7.x**: preview e edição visual.
- **Python + pywebview**: host desktop/bridge.
- **Pillow**: render final determinístico sobre as fotos originais.
- **JSON Schema**: contratos Template/Job.
- **PyInstaller + Inno Setup**: distribuição Windows.
- **Windows context menu V1**: shell verb clássico; V2 moderna opcional com `IExplorerCommand`/MSIX.

O projeto não forkará um editor estilo Canva inteiro. Fabric é o motor; editores open source são referências para lifecycle, history, crop e UX.

## Estrutura

```text
.
├── AGENTS.md
├── PLAN.md / STATUS.md / DECISIONS.md
├── .agents/
│   ├── agents/
│   ├── rules/
│   └── skills/
├── apps/
│   ├── ui/
│   └── desktop/
├── templates/
├── schemas/
├── installer/
├── tests/
├── scripts/
└── docs/
    ├── adr/
    └── audits/
```

## Antigravity 2.19.1

A organização foi auditada contra a documentação atual do Antigravity 2.0:
- regras por diretório para reduzir contexto always-on;
- Skills em `.agents/skills` com progressive disclosure;
- Custom Agents com model/policy/skills explícitos;
- nenhum novo workflow legado;
- CI valida frontmatter e estrutura das customizações.

Leia `docs/ANTIGRAVITY.md` e `docs/audits/ANTIGRAVITY_2_19_1_FORENSIC_AUDIT.md`.

## Bootstrap / validação

```bash
python -m pip install -e ".[dev]"
python scripts/verify_repo.py
pytest -q
```

## Privacidade

Não versionar fotografias reais de clientes, caminhos pessoais, credenciais, outputs de produção ou screenshots com pessoas. Somente assets gráficos sem foto e fixtures sintéticas entram no Git.

## Licença

Código proprietário da EVYDÊNCIA. Dependências e projetos de referência mantêm suas próprias licenças.
