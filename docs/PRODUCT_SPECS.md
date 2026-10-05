# Product Specifications

## Abordagem de composição por produto (decidido em 2026-10-03)

| Produto | Base | Fotos | Overlay |
|---|---|---|---|
| Calendário | canvas branco | sob o overlay | PNG transparente fornecido pelo estúdio |
| Chaveiro | canvas branco **gerado pelo renderer** no tamanho físico | sobre o fundo | nenhum |
| Globo | canvas branco **gerado pelo renderer** no tamanho físico | sobre o fundo | nenhum |

Por que não criar PNG de moldura para Chaveiro/Globo:
- o canvas é derivado de mm + DPI; um PNG fixo teria resolução própria e poderia divergir do DPI de produção;
- nada para versionar/atualizar quando DPI ou margens mudarem: só o template muda;
- o modelo já suporta `overlay: null` sem mudança de schema.

Evolução opcional (não implementada): guias de corte finas ou cor de fundo por template exigem schema 1.1 + ADR; só após validação com o laboratório.

## Chaveiro 3x4
Confirmado pelo usuário:
- folha: 216 × 152 mm;
- foto: 34 × 44 mm;
- grade: 6 colunas × 3 linhas = 18 slots;
- 1 chaveiro usa 2 fotos (frente/verso);
- cada slot deve ser substituível individualmente;
- foto precisa pan/zoom/rotação simples.

Derivado matematicamente, ainda não aprovado em prova física:
- grid ocupa 204 × 132 mm;
- se centralizada: margens laterais 6 mm e verticais 10 mm.

Informado em 2026-10-03:
- usuário descreveu "21,6 cm altura × 15,2 cm largura; foto 3,4 cm altura × 4,4 cm largura" (folha retrato, fotos paisagem);
- a imagem-exemplo enviada mostra a **mesma geometria rotacionada 90°**: folha paisagem 216 × 152 mm com 6 × 3 fotos retrato 34 × 44 mm; margens visuais ≈ 6 mm laterais e ≈ 10 mm verticais (corrobora a derivação acima, sem substituir prova física).

Pendente:
- **orientação do arquivo de saída esperado pelo laboratório** (paisagem 216×152 ou retrato 152×216);
- pareamento físico exato frente/verso;
- confirmar margens/offset de impressão;
- DPI.

## Calendário 2027
Confirmado:
- um overlay PNG transparente;
- uma foto por baixo;
- operador precisa pan/zoom/rotação;
- saída na **mesma pasta da foto original**, nome `Calendario_<nome original>` (colisão → sufixo numérico, nunca sobrescreve).

Overlay recebido em 2026-10-03 (arquivo local do estúdio, ainda não versionado):
- PNG RGBA 1067 × 1474 px, metadado 72 dpi (proporção 1 : 1,3814);
- janela da foto (alpha = 0): px x 119–940, y 108–501; incluindo borda antialias (alpha < 250): px x 113–945, y 100–507;
- pergaminho fora da janela tem alpha 252–253 (≈1 % translúcido), não 255.

Pendente:
- canvas físico (cm) — a proporção px é compatível com 21 × 29 cm, mas **não confirmado**;
- DPI de produção — 1067 px de largura equivalem a ~129 dpi em 21 cm; para 300 dpi o overlay precisaria de ~2480 × 3425 px;
- slot físico (deriva-se da janela em px assim que canvas físico for confirmado);
- asset final aprovado no repositório.

## Globo de neve
Confirmado (Measured):
- canvas: 152 × 102 mm (paisagem, 10×15 cm fotográfico, 1795 × 1205 px @ 300 DPI);
- duas fotos verticais;
- cada foto: 50 × 80 mm (largura × altura);
- pan/zoom/rotação por foto;
- sem overlay; fundo branco gerado pelo renderer com guias sutis de corte.

Layout assimétrico (Image-Derived) — template v1.1.0:
- par lado a lado derivado de fotografia de referência do laboratório:
- foto_1: x = 16,7 mm, y = 10,2 mm (w=50 mm, h=80 mm);
- foto_2: x = 73,7 mm, y = 10,2 mm (w=50 mm, h=80 mm);
- gap entre fotos: 7,0 mm;
- margem esquerda: 16,7 mm, margem direita: 28,3 mm;
- margem superior: 10,2 mm, margem inferior: 11,8 mm.

Pendente:
- confirmação vetorial numérica via arquivo CorelDRAW / gabarito oficial do laboratório.

## Integração de Shell Windows 11
- **Menu Moderno**: Integração nativa via interface COM `IExplorerCommand` e *Sparse Package Identity / Sparse MSIX* (`MODERN_MENU_VISIBLE = supported`).
- **Ícone e Visibilidade**: O comando "Gerar com EVYDÊNCIA" aparece no primeiro menu de contexto moderno do Windows 11 com ícone de alta resolução.
- **Posicionamento**: O Windows 11 agrupa comandos em categorias de sistema; a API não oferece flag para forçar extensões de terceiros acima dos verbos nativos de sistema ("Abrir", "Abrir com"). Alterações invasivas de associação de arquivo (.jpg/.png) são estritamente rejeitadas para preservar a integridade do sistema operacional.

## Regra de status
Enquanto houver geometria necessária pendente, template fica `draft`. `production` exige prova física e provenance.pending vazio. Templates industriais homologados possuem proteção de Geometria de Produção Fixa no Gestor.
