# Windows Integration

## V1 — recomendada
Usar um shell verb clássico registrado pelo Inno Setup em `HKA\Software\Classes`.

Fluxo:
`Explorer -> EvydenciaPrintGenerator.exe "%1" -> valida path -> abre UI`

Aceitamos inicialmente a entrada em **Mostrar mais opções** no Windows 11. O objetivo do MVP é confiabilidade, não shell extension nativa.

Requisitos:
- quoting correto;
- Unicode/acentos;
- espaços;
- caminho longo;
- arquivo inexistente/corrompido;
- app aberto sem argumento;
- instalação/desinstalação reversível;
- sem privilégios administrativos desnecessários.

## V2 — menu moderno Windows 11
Avaliar somente após MVP:
- `IExplorerCommand`;
- sparse MSIX;
- signing;
- filtro por tipo;
- rollback e suporte Win10/11.

Referência Microsoft PowerToys:
https://github.com/microsoft/PowerToys/blob/main/doc/devdocs/common/context-menus.md

A documentação do PowerToys mostra o padrão dual: classic `IContextMenu`/registry para compatibilidade e `IExplorerCommand` + MSIX para o menu moderno.

## Segurança
Nenhuma decodificação/render de imagem acontece em `explorer.exe`. O shell somente inicia um processo separado.
