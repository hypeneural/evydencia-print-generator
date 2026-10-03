---
name: windows-shell-integration
description: Projeta e valida integração com Explorer, linha de comando, pywebview, PyInstaller e Inno Setup. Use ao criar menu de contexto, installer ou fluxo de abertura de imagens no Windows.
---
# Windows Shell Integration

## Arquitetura em fases

### V1 — shell verb clássico
- Registre via instalador em `HKA\Software\Classes`.
- O shell apenas executa o app com caminho(s) citado(s); não processa imagem dentro de Explorer.
- Aceite que no Windows 11 a entrada possa aparecer em **Mostrar mais opções**.
- O app precisa funcionar também aberto sem argumento.

### V2 — menu moderno do Windows 11
Só avaliar depois do MVP estável. A referência oficial de implementação é Microsoft PowerToys: sparse MSIX + `IExplorerCommand`, com signing e registro próprios.

## Contrato de lançamento
- Executável: `EvydenciaPrintGenerator.exe`.
- Argumentos devem ser tratados como entrada não confiável.
- Validar existência, extensão/assinatura real e arquivos suportados.
- Não persistir caminho completo em logs normais.

## Matriz mínima de teste
- Windows 10/11 suportado pelo produto.
- JPG/JPEG/PNG.
- caminho com espaços.
- acentos/Unicode.
- caminho longo.
- arquivo inexistente/corrompido.
- abrir app diretamente.
- instalar → usar → desinstalar → confirmar remoção da chave.
- múltipla seleção somente quando contrato e registro forem explicitamente implementados/testados.

Referência: `docs/WINDOWS_INTEGRATION.md`.
