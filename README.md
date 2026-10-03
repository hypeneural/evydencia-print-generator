# EVYDÊNCIA Print Generator

[![CI](https://github.com/hypeneural/evydencia-print-generator/actions/workflows/ci.yml/badge.svg)](https://github.com/hypeneural/evydencia-print-generator/actions/workflows/ci.yml)

Aplicativo desktop Windows local para compor produtos fotográficos de impressão da EVYDÊNCIA por templates e slots de foto, com fluxo simples para o operador e configuração controlada para o gestor.

## Fluxo alvo
1. Botão direito sobre uma foto no Windows → **Gerar com EVYDÊNCIA**.
2. Escolher produto: Calendário, Chaveiro ou Globo.
3. Ajustar cada foto com arrastar, zoom e rotação dentro do slot.
4. Gerar arquivo final sem alterar a fotografia original.

## Produtos iniciais
| Produto | Canvas físico | Slots | Estado |
|---|---:|---:|---|
| Chaveiro 3x4 | 216 × 152 mm | 18 (6×3), 34 × 44 mm | draft; prova física pendente |
| Calendário 2027 | dimensão física a confirmar | 1 | draft; overlay/pan/zoom/rotação |
| Globo de neve | 152 × 102 mm | 2 × 50 × 80 mm | draft; X/Y pendentes |

## Arquitetura
- **React + TypeScript + Fabric.js**: preview e edição visual.
- **Python + pywebview**: host desktop/bridge.
- **Pillow**: render final determinístico sobre as fotos originais.
- **JSON Schema**: contratos Template/Job.
- **PyInstaller + Inno Setup**: distribuição Windows.
- **Windows V1**: shell verb clássico; V2 moderna opcional com `IExplorerCommand`/MSIX.

O projeto não forkará um editor estilo Canva inteiro. Fabric é o motor; editores open source são referências de UX/arquitetura.

## AntiGravity 2.19.1
O repositório foi estruturado para progressive disclosure:
- root `AGENTS.md` enxuto;
- `AGENTS.md` por domínio;
- Rules condicionais;
- 8 Skills focadas;
- `evydencia-builder` + 5 subagentes;
- hook de validação;
- `/plan` nativo para mudanças não triviais.

Leia:
- `docs/ANTIGRAVITY.md`
- `docs/audits/ANTIGRAVITY_2_19_1_FORENSIC_AUDIT.md`
- `docs/ARCHITECTURE.md`
- `docs/PRODUCT_SPECS.md`
- `docs/WINDOWS_INTEGRATION.md`

## Validação
```bash
python -m pip install -e ".[dev]"
python scripts/verify_repo.py
pytest -q
ruff check apps/desktop/src tests scripts
```

CI roda em Ubuntu e Windows.

## Privacidade
Não versionar fotografias reais de clientes, caminhos pessoais, credenciais ou outputs de produção.

## Licença
Código proprietário da EVYDÊNCIA; dependências mantêm suas próprias licenças.
