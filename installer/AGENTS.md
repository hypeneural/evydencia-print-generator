# Windows Installer / Shell Rules

- V1 usa shell verb simples que inicia o executável; nenhuma DLL de imagem dentro de explorer.exe.
- Instalação/desinstalação reversível.
- Preferir HKA\Software\Classes no Inno Setup.
- Citar executável e argumento.
- Aceitar Show more options no Windows 11 na V1.
- IExplorerCommand + sparse MSIX é Fase 2.
- Não pedir admin sem necessidade.
- Testar Unicode, espaços, caminho longo, abrir sem args e uninstall.

Use /windows-shell-integration.
