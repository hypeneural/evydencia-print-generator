# EVYDÊNCIA Print Generator

[![CI](https://github.com/hypeneural/evydencia-print-generator/actions/workflows/ci.yml/badge.svg)](https://github.com/hypeneural/evydencia-print-generator/actions/workflows/ci.yml)

Editor desktop Windows local para produzir Calendário, Chaveiro e Globo com fluxo extremamente simples para o operador e templates configuráveis pelo gestor.

## Fluxo alvo
1. Botão direito numa foto → **Gerar com EVYDÊNCIA**.
2. Escolher produto.
3. Ajustar foto(s) visualmente: arrastar, zoom, rotação, substituir.
4. Gerar arquivo final com o **original**, sem alterar a origem.

Também aceita **Adicionar fotos** e drag-and-drop dentro do app.

## Princípio de performance e qualidade
**Editar leve, renderizar original.**

O Fabric.js recebe previews/proxies leves e deduplicados. O Python/Pillow reabre o original somente no render final. Assim o editor permanece fluido sem usar o preview como arquivo de impressão.

## Modos

### Operador
Sem layers genéricas, pixels ou DPI:
- source tray;
- selecionar slot;
- substituir;
- pan/crop;
- zoom;
- rotação;
- reset;
- undo/redo;
- ações específicas do produto;
- gerar.

### Gestor
Ferramentas estruturais:
- canvas em mm;
- criar/redimensionar slots;
- layer order;
- trazer para frente/enviar para trás;
- lock/visibility;
- overlays/assets;
- groups;
- guides/snap;
- validar/publicar template.

## Produtos iniciais
| Produto | Canvas físico | Slots | Estado |
|---|---:|---:|---|
| Chaveiro 3x4 | 216 × 152 mm | 18 (6×3), 34 × 44 mm | draft; prova física pendente |
| Calendário 2027 | dimensão física a confirmar | 1 | primeiro vertical slice |
| Globo de neve | 152 × 102 mm | 2 × 50 × 80 mm | canonical 152×102; prova física pendente |

## Stack
- React + TypeScript + Fabric.js 7.x
- Python + pywebview 6.x
- Pillow 12.x
- JSON Schema
- PyInstaller + Inno Setup
- Windows V1: classic shell verb; menu moderno opcional depois

## AntiGravity 2.19.1
Estrutura otimizada para progressive disclosure:
- root `AGENTS.md` curto;
- AGENTS por domínio;
- Rules condicionais;
- **12 Skills focadas**;
- `evydencia-builder` + **6 subagentes especialistas**;
- hook de validação;
- `/plan` para feature transversal;
- `/grill-me` para requisito ambíguo;
- auditor independente antes de merge/release.

## Próximo marco
Issue **#4 — SourceRegistry + Preview Pipeline + Renderer do Calendário**.

Ordem:
1. ingest/source registry;
2. preview proxy/cache;
3. renderer determinístico;
4. Calendário no Fabric;
5. parity + performance;
6. depois Chaveiro/Globo;
7. modo Gestor por último.

## Documentação principal
- `docs/ANTIGRAVITY.md`
- `docs/EDITOR_UX.md`
- `docs/IMAGE_PIPELINE.md`
- `docs/PERFORMANCE_BUDGETS.md`
- `docs/EDITOR_IMPLEMENTATION_PLAN.md`
- `docs/PRODUCT_SPECS.md`
- `docs/WINDOWS_INTEGRATION.md`
- `docs/audits/ANTIGRAVITY_2_19_1_EDITOR_FORENSIC_AUDIT.md`

## Validação
```bash
python -m pip install -e ".[dev]"
python scripts/verify_repo.py
pytest -q
ruff check apps/desktop/src tests scripts
```

CI roda em Ubuntu e Windows.

## Privacidade
Não versionar fotos reais de clientes, caminhos pessoais, credenciais ou outputs de produção.

## Licença
Código proprietário da EVYDÊNCIA; dependências mantêm suas próprias licenças.
