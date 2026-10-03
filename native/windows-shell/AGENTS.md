# Native Windows Shell Rules

Este diretório roda no caminho do File Explorer. Trate estabilidade e latência como requisitos de segurança.

## Stack
- C++20/Win32/COM
- IExplorerCommand
- x64
- sparse MSIX
- build separado do Python app

## Proibido no shell DLL
- Python runtime
- Pillow
- WebView/pywebview
- Fabric/JS
- rede
- decodificação de imagem
- EXIF/ICC
- hashing de arquivo
- banco
- espera por processo

## Métodos rápidos
`GetTitle`, `GetIcon`, `GetState`, `GetFlags` precisam ser bounded e não-bloqueantes.

## Invoke
Só extrai seleção e lança processo externo. Trabalho real começa no app.

## Compatibilidade
Alvo primário: Windows 11 Home 25H2 x64.
Classic fallback pertence ao installer, não à DLL moderna.

Use /windows-shell-integration.
