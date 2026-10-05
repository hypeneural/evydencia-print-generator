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
- Escape: sair de modo de ajuste;
- Ctrl+Z/Ctrl+Y: history;
- overlay/slot estrutural nunca se move no Operador.

## Calendário
- canvas retrato 1067×1474;
- overlay ocupa 100% da visualização e fica bloqueado;
- foto inicia em cover centralizado;
- nenhuma área branca deve aparecer dentro da abertura;
- pan/zoom/rotação afetam apenas a foto;
- double-click/Enter pode focar/alternar modo Ajustar.

## Chaveiro
- canvas paisagem 216×152 mm;
- 18 slots em 6×3;
- cada slot mantém source + transform independente;
- **Preencher folha** continua disponível;
- double-click em slot preenchido duplica o SlotEditState inteiro para o próximo slot, preservando enquadramento e tornando o destino ativo;
- uma duplicação = uma entrada de undo;
- deve existir alternativa visível ao gesto para acessibilidade.

## Globo
- canvas paisagem 216×102 mm (2551×1205 px @ 300 DPI);
- dois slots 50×80 mm lado a lado (x=54.5 mm e x=111.5 mm, gap 7 mm centralizado);
- **Usar mesma foto nos dois** continua disponível;
- double-click em slot preenchido copia o SlotEditState inteiro para o outro slot;
- depois da cópia, cada slot pode ser ajustado independentemente.

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
