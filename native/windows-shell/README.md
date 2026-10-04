# Native Windows Shell Extension

Subprojeto C++20 x64 responsável pela integração com o menu de contexto moderno do Windows 11.

## Estrutura implementada

```text
native/windows-shell/
├── AGENTS.md
├── CMakeLists.txt
├── README.md
├── src/
│   ├── Guids.h
│   ├── ExplorerCommand.h
│   ├── ExplorerCommand.cpp
│   ├── DllMain.cpp
│   └── EvydenciaShellExtension.def
├── package/
│   ├── AppxManifest.xml
│   └── Assets/
│       ├── StoreLogo.png
│       ├── Square150x150Logo.png
│       └── Square44x44Logo.png
└── tests/
    └── contract/
        └── test_shell_extension.cpp
```

## Contrato de Execução

A DLL opera exclusivamente como disparador ultra-leve:
1. `GetState` inspeciona a extensão dos arquivos selecionados (`.jpg`, `.jpeg`, `.png`) sem I/O pesado de disco nem decodificação de imagem.
2. `Invoke` extrai os caminhos via `IShellItemArray` e dispara o executável com a seleção (via argumentos diretos ou arquivo temporário de manifest `--shell-request` quando a seleção for grande).
3. Explorer nunca carrega Python, Pillow ou WebView em seu processo.

## Comandos de Build & Teste

```powershell
# Compilar DLL e rodar testes de contrato C++
python scripts/build_shell_extension.py

# Empacotar e assinar pacote sparse MSIX
powershell -ExecutionPolicy Bypass -File scripts/package_sparse_msix.ps1

# Gerenciar registro (moderno ou fallback clássico)
python scripts/manage_shell_extension.py status
python scripts/manage_shell_extension.py install --auto
```
