# EVYDÊNCIA Print Generator

Aplicativo desktop Windows local para compor produtos fotográficos de impressão da EVYDÊNCIA por templates e slots de foto, com fluxo simples para o operador e configuração controlada para o gestor.

## Fluxo alvo
1. Botão direito sobre uma foto no Windows → **Gerar com EVYDÊNCIA**.
2. Escolher produto: Calendário, Chaveiro ou Globo.
3. Ajustar cada foto com arrastar, zoom e rotação dentro do slot.
4. Gerar arquivo final sem alterar a fotografia original.

## Produtos iniciais
| Produto | Canvas físico | Slots | Estado |
|---|---:|---:|---|
| Chaveiro 3x4 | 216 × 152 mm | 18 (6×3), 34 × 44 mm | geometria conhecida; pareamento precisa prova física |
| Calendário 2027 | dimensão física a confirmar | 1 | overlay PNG recebido; pan/zoom/rotação |
| Globo de neve | 152 × 102 mm | 2 × 50 × 80 mm | posições X/Y pendentes |

## Arquitetura
- React + TypeScript + Fabric.js 7.x.
- Python + pywebview.
- Pillow para render final.
- JSON Schema para Template/Job.
- PyInstaller + Inno Setup.
- Context menu V1 por shell verb clássico; V2 moderna opcional com IExplorerCommand/MSIX.

## Antigravity 2.19.1
A organização foi auditada contra a documentação atual do Antigravity 2.0: regras por diretório, Skills com progressive disclosure, Custom Agents especializados, zero workflows novos e validação automática das customizações.

Leia `docs/ANTIGRAVITY.md` e `docs/audits/ANTIGRAVITY_2_19_1_FORENSIC_AUDIT.md`.

## Validação
```bash
python -m pip install -e ".[dev]"
python scripts/verify_repo.py
pytest -q
```

## Privacidade
Não versionar fotografias reais de clientes, caminhos pessoais, credenciais ou outputs de produção.

## Licença
Código proprietário da EVYDÊNCIA; dependências mantêm suas próprias licenças.
