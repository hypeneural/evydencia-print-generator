# PowerToys shell-extension patterns

Reference:
https://github.com/microsoft/PowerToys/blob/main/doc/devdocs/common/context-menus.md

Useful patterns:
- modern Windows 11: sparse MSIX + IExplorerCommand;
- classic compatibility: registry/IContextMenu or static verb;
- PowerRename/ImageResizer use dual registration for reliability;
- modern sparse package requires signing;
- modern handler may be loaded in DllHost; keep it tiny;
- GetState controls visibility/filtering;
- Invoke launches real module/app work outside menu construction.

Installer reference:
https://github.com/microsoft/PowerToys/blob/main/doc/devdocs/core/installer.md

PowerToys defaults to per-user installation and uses sparse MSIX for Windows 11 handlers.

Project adaptation:
- prefer modern handler on Win11;
- keep classic fallback without duplicate visible entries when modern is healthy;
- app work remains out-of-process;
- do not import the PowerToys architecture wholesale.
