# ADR-012 — Espaço de Cor Canônico sRGB para Preview e Produção

**Status:** Aceito (M3 / Image Pipeline Hardening)

## Contexto
O EVYDÊNCIA Print Generator recebe fotografias de câmeras digitais profissionais (ex.: Canon EOS com prefixo `0M4A`, Nikon, Sony), smartphones e scanners. Esses arquivos frequentemente possuem perfis de cor embutidos de gamut alargado (ex.: **Rec. 2020**, **Adobe RGB**, **Display P3**) ou chegam sem perfil ICC mas com metadados EXIF `ColorSpace`.

Em contrapartida:
1. Overlays e molduras decorativas dos produtos (ex.: `calendar-2027-overlay.png`, `polaroid-moldura.png`) são assets gráficos rasterizados em espaço padrão **sRGB**, sem perfil ICC embutido.
2. Minilabs fotográficos comerciais (Noritsu, Fuji Frontier, impressoras dye-sub DNP, Epson SureLab) assumem por padrão que arquivos de entrada enviados para impressão direta em papel fotográfico são codificados estritamente em **sRGB IEC61966-2.1**.
3. O editor web moderno (Chromium / Edge WebView2 via Fabric Canvas 2D) decodifica proxies de imagem no espaço de cor sRGB da tela.

No código legado (`compose.py`), o renderer adotava a política "primeiro ICC vence": extraía os bytes brutos do perfil ICC da primeira foto encontrada (`primary_icc`) e colava os pixels da foto diretamente sobre o canvas branco, sem qualquer conversão de cor. O overlay sRGB era então composto sobre o mesmo canvas, e o JPEG de saída era etiquetado com o `primary_icc`.

Isso gerava dois problemas críticos em produção:
- **Mistura de espaços de cor no mesmo arquivo:** Pixels da foto (em Rec. 2020) coexistiam com pixels da moldura (em sRGB).
- **Desvio de cor em minilabs e visualizadores sem gerenciamento wide gamut:** Ao tratar dados Rec. 2020 como sRGB, tons de pele humana sofriam desvios perceptíveis para vermelho/magenta. Além disso, em produtos multi-slot (ex.: Chaveiro 18 slots), uma foto sRGB gravada sob etiqueta Rec. 2020 tornava-se hiper-saturada e avermelhada.
- **Disparidade de preview vs produção:** O operador visualizava no preview uma aproximação sRGB corrigida pelo navegador, mas a saída final exportava bytes divergentes.

## Decisão

1. **Espaço Canônico de Trabalho (*Working Space*) e de Saída (*Output Space*):**
   O espaço de cor canônico universal do EVYDÊNCIA Print Generator é fixado em **sRGB IEC61966-2.1**.

2. **Normalização na Ingestão / Composição via LittleCMS:**
   Todos os insumos gráficos (fotos de clientes e arquivos de overlay) são convertidos para o espaço sRGB imediatamente após serem abertos, utilizando a biblioteca LittleCMS integrada no Pillow (`PIL.ImageCms`).

3. **Intenção de Renderização:**
   A conversão utiliza a intenção **Colorimétrica Relativa** com compensação de ponto preto (`ImageCms.Intent.RELATIVE_COLORIMETRIC`). Isso mapeia brancos e pretos para o padrão D65 do sRGB preservando com máxima fidelidade as tonalidades cromáticas internas e tons de pele.

4. **Preservação de Transparência (Canal Alfa):**
   Para imagens em modo `RGBA` (especialmente overlays e slots com máscara), o canal alfa é estritamente preservado durante a transformação de cor.

5. **Tratamento de Imagens sem Perfil (Untagged):**
   Imagens raster sem perfil ICC embutido são tratadas canonicamente como sRGB, em total conformidade com a especificação CSS Color 4 e as normas da W3C.

6. **Resiliência e Fail-Safe:**
   Se um arquivo contiver bytes de perfil ICC corrompidos ou não suportados que disparem exceções no LittleCMS (`PyCMSError`), o pipeline registra um alerta detalhado em log e mantém os dados da imagem em sRGB sem interromper a execução nem causar crash no aplicativo.

7. **Etiquetagem Explícita de Saída:**
   Todo arquivo de produção (JPEG) gerado pelo motor embute obrigatoriamente o perfil ICC sRGB canônico padronizado (588 bytes), garantindo consistência determinística em qualquer software gráfico ou impressora de minilab.

8. **Paridade com o Preview do Editor:**
   O serviço de geração de proxies de preview (`ingest/preview.py`) também converte as imagens para sRGB antes de salvar o JPEG no cache local. Isso assegura 100% de paridade cromática entre o que o operador vê no monitor e o arquivo físico impresso.

## Consequências
- Fim definitivo da política "primeiro ICC vence".
- Eliminação do desvio avermelhado em tons de pele ao utilizar câmeras profissionais em espaço estendido.
- Paridade visual absoluta entre o preview no WebView2 e o arquivo de impressão exportado.
- Invalidação automática dos caches de preview legados (`PREVIEW_CACHE_VERSION = "2"`).
- O desempenho é mantido com folga dentro do orçamento: a conversão sRGB adiciona menos de 30 ms por foto.
