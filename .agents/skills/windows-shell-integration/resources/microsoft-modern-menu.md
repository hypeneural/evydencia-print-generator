# Microsoft modern File Explorer context menu

Validated 2026-10-03.

Official documentation:
https://learn.microsoft.com/windows/apps/desktop/modernize/integrate-packaged-app-with-file-explorer

Key facts:
- Windows 11 modern menu uses `IExplorerCommand`.
- Command is registered through `windows.fileExplorerContextMenus`.
- COM class is registered as `windows.comServer`.
- unpackaged Win32 apps may use sparse package identity.
- DLL architecture must match Explorer architecture.
- `GetTitle/GetIcon/GetState` run on Shell UI path and must stay fast.
- `desktop5:ItemType Type="*"` can target files and GetState can filter.
- `Directory` and `Directory\Background` are distinct item types.
- after package update, Explorer may need restart/sign-out to reload registration.

Official API:
https://learn.microsoft.com/windows/win32/api/shobjidl_core/nn-shobjidl_core-iexplorercommand
