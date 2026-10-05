# Editor UX — Operador e Gestor

## Objetivo
Ser mais simples que um editor genérico e seguro para produção fotográfica.

## Operador
Fluxo principal:
```text
abrir/adicionar foto -> escolher produto -> ajustar -> gerar
```

A superfície mínima contém:
- fotos do cliente;
- canvas;
- slot ativo;
- trocar/remover;
- zoom;
- rotação;
- reset;
- undo/redo;
- ações específicas do produto;
- gerar.

### Interação comum
- click no slot: selecionar;
- drag no slot preenchido: mover somente a foto;
- wheel no slot ativo: zoom;
- Delete: remover a foto do slot ativo (somente no Chaveiro e Globo). A foto permanece disponível na bandeja (tray) e o arquivo original nunca é excluído. Ctrl+Z restaura a foto e seu enquadramento exato;
- Escape: sair de modo de ajuste;
- Ctrl+Z/Ctrl+Y: history (1 ação em lote ou individual = 1 entrada no histórico);
- overlay/slot estrutural nunca se move no Operador.
- **Ajuste fino de rotação**: slider (-180° a +179°, passo 1°), campo numérico com precisão de 0.1°, botões rápidos (↶ -90° / ↷ +90°) e indicador de ângulo (`Rotação: X.X°`). Coalescência de histórico: o arrasto contínuo do slider ou digitação atualiza o canvas em tempo real e consolida exatamente 1 entrada de Undo ao soltar o cursor (`onPointerUp`) ou confirmar (`Enter`/`onBlur`).

## Calendário
- canvas retrato 1067×1474;
- overlay ocupa 100% da visualização e fica bloqueado;
- foto inicia em cover centralizado;
- nenhuma área branca deve aparecer dentro da abertura;
- pan/zoom/rotação afetam apenas a foto;
- double-click/Enter pode focar/alternar modo Ajustar;
- tecla Delete não é habilitada no Calendário (remoção via botão "Remover foto" explícito).

## Chaveiro
- canvas paisagem 216×152 mm;
- 18 slots em 6×3;
- cada slot mantém source + transform independente;
- tecla Delete: remove a foto do slot ativo, mantendo a foto na bandeja;
- **Multi-seleção com Shift + clique**: permite selecionar múltiplos slots simultaneamente no Chaveiro. O slot primário mantém a borda azul ativa e os slots secundários exibem borda ciano pontilhada (`#06b6d4`). O clique com Shift não inicia arrasto de foto;
- **Duplicação em lote (`⧉ Duplicar selecionados (N)`)**: duplica as fotos e enquadramentos dos slots selecionados para os próximos slots vazios disponíveis (com wrap-around), gerando exatamente 1 entrada de Undo;
- **⚡ Preencher restantes**: preenche estritamente os slots vazios utilizando a foto e o transform completo do slot ativo. O botão exibe a contagem de slots vazios (`⚡ Preencher restantes (N)`) e permanece desabilitado se o slot ativo não possuir foto ou se todos os slots já estiverem preenchidos; não há fallback silencioso para outros slots;
- **Distribuição em lote (Multi-drop)**: arrastar múltiplos arquivos do Windows Explorer ou selecionar múltiplas fotos no diálogo distribui os itens nos slots:
  - drop direto sobre um slot: substitui a foto daquele slot (âncora) com o primeiro item e preenche os próximos slots vazios em ordem (com wrap-around);
  - drop na margem do canvas: preenche os primeiros slots vazios sem sobrescrever slots já ocupados;
  - drop fora do canvas: adiciona as fotos exclusivamente à bandeja sem mutar os slots da folha;
  - fotos que excederem o número de slots vazios permanecem na bandeja sem descarte;
  - cada operação em lote gera exatamente 1 entrada no histórico de Undo (Ctrl+Z);
- double-click em slot preenchido duplica o SlotEditState inteiro para o próximo slot, preservando enquadramento e tornando o destino ativo;
- uma duplicação = uma entrada de undo;
- **Renderização parcial**: o Chaveiro pode ser gerado a partir de 2 ou mais slots preenchidos (os slots vazios permanecem brancos no papel fotográfico, e o nome do arquivo final deriva do primeiro slot preenchido na ordem do gabarito);
- deve existir alternativa visível ao gesto para acessibilidade.

## Polaroid Natal (Draft)
- canvas 82.97×102.02 mm (980×1205 px @ 300 DPI);
- 1 slot de foto (`foto_principal` 71.37×72.98 mm em x=5.84, y=5.00 mm, correspondendo à janela transparente 843×862 px a partir de 69, 59 px);
- overlay PNG obrigatório posicionado na camada superior sem redimensionamento destrutivo;
- exportação JPEG a 95% de qualidade (`Polaroid_<orig>_<hash>.jpg`);
- requer 1 foto preenchida para produção.

## Pós-Renderização e Shell
- **Abertura automática no Windows Explorer**: após a geração do arquivo de produção, a pasta de saída é aberta e o arquivo recém-gerado é automaticamente selecionado via `SHOpenFolderAndSelectItems` (com fallback robusto para `explorer.exe /select,<path>`), sem falhar a renderização caso o Shell do Windows demore a responder.

## Globo
- canvas paisagem 152×102 mm (1795×1205 px @ 300 DPI);
- dois slots 50×80 mm lado a lado (x=16.7 mm e x=73.7 mm, gap 7 mm assimétrico derivado do gabarito físico real, margem direita 28.3 mm);
- tecla Delete: remove a foto do slot ativo (`foto_1` ou `foto_2`), mantendo-a na bandeja e preservando o outro slot;
- **Distribuição em lote**: suporta até a capacidade do template (2 slots). Drop sobre um slot substitui a âncora e preenche o outro se vazio; drop no gap de 7 mm ou nas margens preenche os primeiros slots vazios; excedentes permanecem na bandeja;
- **Usar mesma foto nos dois** continua disponível;
- double-click em slot preenchido copia o SlotEditState inteiro para o outro slot;
- depois da cópia, cada slot pode ser ajustado independentemente.

## Windows 11 — Integração de Shell e Menu de Contexto
- Implementado via `IExplorerCommand` nativo x64 + identidade de pacote esparso (Sparse MSIX);
- O comando aparece no **menu moderno principal** do Windows 11 para formatos suportados (.jpg, .jpeg, .png);
- **Posicionamento no menu**: o Windows Explorer agrupa extensões de terceiros abaixo dos comandos nativos do Shell (Abrir, Abrir com, etc.). A API pública `IExplorerCommand::GetFlags` (`EXPCMDFLAGS`) não oferece flags de ordenação ou prioridade absoluta (`MODERN_MENU_VISIBLE = PASS`, `ABSOLUTE_FIRST_POSITION = UNSUPPORTED_BY_PUBLIC_API`);
- A flag `Position=Top` é restrita aos verbos estáticos do menu clássico/legado (Shift+F10 / Mostrar mais opções), já configurada no instalador de fallback (`shell_fallback.py`).


## Viewport
Preview deve manter a proporção física em qualquer janela. Ver docs/UI_RUNTIME_ARCHITECTURE.md.
Resize não altera Job.

## Estados obrigatórios
- empty;
- loading preview sem bloquear janela;
- source error com retry/remove;
- rendering sem congelar UI;
- success com caminho + Abrir pasta;
- collision-safe, sem overwrite silencioso.

## Gestor (Marco M5)
Separado do Operador através de controle de modo no cabeçalho superior (`Operador` | `Gestor`), utilizando o **Shared Editor Runtime** (`ProductCanvas.tsx` com capabilities distintas) e modelo efêmero `TemplateDraft`.

### Princípios e Interações do Gestor:
- **Milímetros (mm) como Fonte da Verdade**: Todas as entradas e inspeções no painel do Gestor utilizam milímetros físicos (`x_mm`, `y_mm`, `width_mm`, `height_mm`).
- **Coordenadas Derivadas**: Coordenadas em pixels (`rect_px`) são estritamente calculadas via `mm_to_px(mm, dpi)`.
- **Seleção e Bounding Box**: O slot ativo exibe borda destacada e 4 alças de redimensionamento nos cantos (`NW`, `NE`, `SE`, `SW`).
- **Manipulação Direta**: Arrastar o corpo do slot desloca a posição em milímetros; arrastar os cantos redimensiona a largura e altura com restrição aos limites da folha.
- **Inspector Contextual (Progressive Disclosure)**:
  - Folha/Canvas: dimensões físicas em mm, DPI e alternância de orientação;
  - Slot Ativo: ID, coordenadas e dimensões em mm, proporção, modo de enquadramento (`cover`/`fit`) e permissões do Operador (`allow_pan`, `allow_zoom`, `allow_rotate`);
  - Overlay: inspeção de caminho de máscara decorativa;
  - Validação em Tempo Real: feedback visual imediato (`validateTemplateDraft`) garantindo que nenhum slot exceda os limites físicos da folha ou possua ID duplicado.
- **Imutabilidade em Disco**: O Gestor edita uma instância em memória (`TemplateDraft`). A publicação e gravação versionada em disco ocorre no Marco M5-B.

## Acessibilidade
- foco visível;
- alvos confortáveis;
- gesto sempre tem alternativa por botão/teclado quando essencial;
- labels em português operacional;
- 1024×680 continua funcional e Gerar não desaparece.
