# Native Windows Shell Extension

Futuro subprojeto C++ responsável pelo menu moderno do Windows 11.

## Deliverables previstos

```text
native/windows-shell/
├── AGENTS.md
├── CMakeLists.txt
├── src/
│   ├── ExplorerCommand.cpp
│   ├── ExplorerCommand.h
│   ├── DllMain.cpp
│   └── resource.rc
├── package/
│   └── AppxManifest.xml
└── tests/
    └── contract/
```

## Contrato

A DLL não edita foto. Ela somente:
1. decide se o comando deve aparecer;
2. recebe a seleção;
3. lança o executable principal;
4. retorna ao Explorer.

Antes de implementar, leia `docs/WINDOWS_CONTEXT_MENU_PRO.md`.
