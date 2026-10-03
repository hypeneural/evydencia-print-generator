# Editor UX — Operador e Gestor

## Objetivo
Ser mais simples que um editor genérico e mais seguro para produção fotográfica. A tela deve ensinar o fluxo sem treinamento técnico.

## Modo Operador

### Layout
```text
┌ Produto / quantidade ───────────────────── Undo Redo ┐
│                                                     │
│ FOTOS        CANVAS / PRODUTO          AJUSTAR      │
│ [+ fotos]    ┌──────────────────┐       Trocar       │
│ thumb A      │                  │       Zoom  ─●+    │
│ thumb B      │   slot ativo     │       Girar -  +   │
│ thumb C      │                  │       Reset        │
│              └──────────────────┘                    │
│                                                     │
│                         [ GERAR ARQUIVO ]            │
└─────────────────────────────────────────────────────┘
```

### Interação
- abrir pelo menu de contexto já adiciona a(s) source(s);
- botão **Adicionar fotos** abre multi-select;
- drag-and-drop no app adiciona sources;
- arrastar thumbnail para slot substitui/preenche;
- click no slot seleciona;
- drag no slot move a foto sob a máscara;
- wheel sobre slot ativo controla zoom;
- double click/Enter entra em **Ajustar foto**;
- Escape encerra ajuste;
- Ctrl+Z/Ctrl+Y sempre disponíveis.

### Sem painel de layers
O Operador não deve mover overlay para trás nem apagar slot. "Frente/verso", duplicação e preenchimento são comandos de produto.

## Chaveiro
Ações primárias:
- quantidade de chaveiros 1–9;
- **Preencher quantidade** com source ativa;
- **Preencher folha**;
- click em qualquer slot → substituir individualmente;
- comando de par frente/verso após o pareamento ser fisicamente confirmado.

## Calendário
- uma foto;
- overlay sempre visível/bloqueado;
- pan/zoom/rotação;
- botão Reset.

## Globo
- dois slots;
- sources independentes;
- ação **Usar mesma foto nos dois**;
- ajuste independente depois.

## Modo Gestor
Ativado explicitamente; não mistura ferramentas com o Operador.

### Ferramentas
- canvas em mm;
- criar/duplicar/excluir slot;
- medidas e posição;
- snap/guias/alinhamento;
- add overlay/background/decorative asset;
- layer list com drag reorder;
- Bring Forward / Send Backward;
- lock/unlock;
- visibility;
- groups e regras de duplicate/fill;
- permissões por slot;
- output/naming;
- validar e publicar versão.

### Segurança
- assets/overlays podem ser protegidos;
- publish falha se houver dimensão/posição necessária pendente;
- toda alteração é undoable;
- produção publicada não é editada in-place: cria nova template_version.

## Estados obrigatórios
- empty: instrução curta + Adicionar fotos;
- loading preview: thumbnail skeleton/progress, canvas continua utilizável;
- source error: card local com retry/remove;
- rendering: progresso não bloqueia leitura/ajuste até o snapshot do Job ser enviado;
- success: caminho do arquivo + Abrir pasta;
- collision: naming automático, sem overwrite silencioso.

## Acessibilidade/ergonomia
- alvos de clique confortáveis;
- foco visível;
- atalhos não dependem apenas de mouse;
- labels em português operacional;
- 1366×768 continua utilizável sem esconder Gerar.
