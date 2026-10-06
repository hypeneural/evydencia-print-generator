# Auditoria de Governança: Tamanho Físico e Resolução do Calendário 2027

**Data:** 06/10/2026  
**Produto:** `calendario-2027`  
**Template Version:** `1.0.0`  
**Status do Template:** `production`  
**Quality Gate G7 (Produção Física):** `PENDING`  

---

## 1. Contexto e Motivação

Durante a revisão de qualidade de imagem do **Calendário 2027**, identificou-se uma discrepância histórica na documentação e anotações do projeto relativa às dimensões físicas da folha, formato de papel fotográfico e densidade de pixels (DPI).

O objetivo desta auditoria é:
1. Registrar formalmente os dados **mensurados** no asset digital de produção fornecido pelo estúdio.
2. Esclarecer as relações matemáticas entre pixels, milímetros e DPI.
3. Comparar as dimensões do template com os formatos físicos padronizados da indústria fotográfica de minilab.
4. Estabelecer o protocolo de governança para manter o Quality Gate G7 como `PENDING` até a validação física no laboratório fotográfico.

---

## 2. Fatos Mensurados Objetivamente

A análise pericial do arquivo mestre de overlay transparente (`templates/calendario-2027/assets/calendar-2027-overlay.png`), inspecionado via Photoshop e via script pericial `scripts/diagnose_image_pipeline.py`, estabelece os seguintes dados irrefutáveis:

| Atributo | Valor Mensurado | Origem / Comprovação |
| :--- | :--- | :--- |
| **Dimensões do Raster** | `1067 × 1474` pixels | Dimensão exata em pixels da imagem PNG (`overlay-2027`) |
| **Resolução Nominal do Asset** | `254 DPI` | Medido no Photoshop sobre o arquivo fornecido pelo estúdio |
| **Resolução Métrica Equivalente** | `10.0 pixels / mm` | $\frac{254 \text{ dots}}{25.4 \text{ mm}} = 10.0 \text{ px/mm}$ exatos |
| **Largura Física Derivada** | `106.7 mm` | $\frac{1067 \text{ px}}{10.0 \text{ px/mm}} = 106.7 \text{ mm}$ |
| **Altura Física Derivada** | `147.4 mm` | $\frac{1474 \text{ px}}{10.0 \text{ px/mm}} = 147.4 \text{ mm}$ |
| **Janela Transparente (Alpha = 0)** | `left=119, top=108, w=821, h=393` px | Medido no Photoshop (abertura exata da moldura) |
| **Slot de Renderização no Template** | `left=118, top=107, w=823, h=395` px | `x=11.8, y=10.7, w=82.3, h=39.5` mm no `template.json` |

> [!NOTE]
> **Explicação da Sangria de 1 Pixel no Slot:**
> O slot no `template.json` foi intencionalmente dimensionado com $823 \times 395$ px ($118, 107$), exatamente 1 pixel maior em cada extremidade do que a abertura vazada ($821 \times 393$). Essa sobreposição de 1 pixel sob a borda da moldura decorativa atua como sangria de segurança (*bleed*), evitando frestas brancas microscópicas entre a foto e a borda da moldura causadas por arredondamentos subpixel.

---

## 3. Comparativo com Padrões Físicos de Impressão e Minilab

Na indústria de impressão fotográfica e gráfica, existem padrões estabelecidos de mídia:

1. **Papel Fotográfico "10x15" (Minilab Fuji Frontier / Noritsu / DNP):**
   - Na realidade, o papel fotográfico tradicional de 4×6 polegadas mede exatamente **$101.6 \times 152.4\text{ mm}$** (comercialmente arredondado para $102 \times 152\text{ mm}$).
   - Se o arquivo do Calendário ($106.7 \times 147.4\text{ mm}$) for enviado para impressão direta em papel 10x15 sem corte:
     - Na largura: $106.7\text{ mm} > 101.6\text{ mm}$ (ocorreria corte de ~5 mm nas laterais se não for ajustado).
     - Na altura: $147.4\text{ mm} < 152.4\text{ mm}$ (sobrariam bordas brancas verticais de ~5 mm).

2. **Padrão A6 (Papel Gráfico / Postcard):**
   - Mede exatamente **$105.0 \times 148.0\text{ mm}$**.
   - É muito próximo de $106.7 \times 147.4\text{ mm}$ (variação de apenas 1.7 mm na largura e 0.6 mm na altura).

3. **Base Comercial do Calendário de Geladeira / Magnético:**
   - O produto físico comercializado pelo estúdio consiste em uma base magnética com calendário destacável colada em manta magnética.
   - O designer do estúdio desenhou a moldura em Photoshop especificamente para casar com a matriz de corte da base magnética fornecida pelo fornecedor de brindes.
   - A escolha de **254 DPI** no Photoshop foi propositalmente calculada para estabelecer a convenção $1\text{ mm} = 10\text{ pixels}$.

---

## 4. Decisão de Governança e Status do Gate G7

1. **Proibição de Alteração Não Autorizada:**
   A geometria digital definida em `templates/calendario-2027/template.json` reflete o asset do Photoshop com exatidão matemática $1:1$. **Nenhum valor milimétrico ou em pixels deve ser alterado ou adivinhado sem validação física direta com o estúdio.**

2. **Classificação do Gate G7:**
   - **G7 Produção Física:** Permanece **`PENDING`**.
   - O gate só poderá ser classificado como `PHYSICAL PASS` após:
     - Impressão real de uma folha de prova no minilab do cliente.
     - Montagem física da foto com a manta magnética / base de calendário.
     - Medição com paquímetro das margens externas e da janela de visualização da fotografia.

3. **Regra de Produção:**
   A aplicação continuará gerando arquivos em $1067 \times 1474$ pixels a 254 DPI em espaço sRGB. Qualquer necessidade de reenquadramento para mídia de minilab 10x15 avulsa será tratada como nova variante de template ou configuração de sangria de laboratório, nunca como mutação silenciosa do produto existente.
