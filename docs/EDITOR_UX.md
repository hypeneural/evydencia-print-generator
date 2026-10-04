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
- canvas paisagem 152×102 mm;
- dois slots 50×80 mm lado a lado;
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

## Gestor
Separado do Operador. Pode editar canvas físico, slots, groups, layers, lock/visibility, overlays/assets, medidas, output e publish/version.

## Acessibilidade
- foco visível;
- alvos confortáveis;
- gesto sempre tem alternativa por botão/teclado quando essencial;
- labels em português operacional;
- 1024×680 continua funcional e Gerar não desaparece.
