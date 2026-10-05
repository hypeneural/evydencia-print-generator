"""Windows Explorer item reveal helper via SHOpenFolderAndSelectItems and CLI fallback."""

from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def reveal_in_explorer(file_path: str | Path) -> bool:
    """Reveal a generated output file in Windows File Explorer with the item selected.

    Uses Windows shell API (SHOpenFolderAndSelectItems via ctypes) with fallback
    to `explorer.exe /select,<path>`.
    Returns True if launch/selection succeeded, False otherwise.
    Never raises exceptions.
    """
    try:
        path = Path(file_path).resolve()
        if not path.is_file():
            logger.warning("reveal_in_explorer: file does not exist: %s", path)
            return False

        if os.name != "nt":
            return False

        # Attempt 1: Official Windows Shell API SHOpenFolderAndSelectItems
        try:
            import ctypes
            from ctypes import wintypes

            ole32 = ctypes.windll.ole32
            shell32 = ctypes.windll.shell32

            # Configure ctypes signatures for 64-bit safety
            shell32.SHParseDisplayName.argtypes = [
                wintypes.LPCWSTR,
                ctypes.c_void_p,
                ctypes.POINTER(ctypes.c_void_p),
                wintypes.DWORD,
                ctypes.POINTER(wintypes.DWORD),
            ]
            shell32.SHParseDisplayName.restype = ctypes.c_long

            shell32.ILFindLastID.argtypes = [ctypes.c_void_p]
            shell32.ILFindLastID.restype = ctypes.c_void_p

            shell32.SHOpenFolderAndSelectItems.argtypes = [
                ctypes.c_void_p,
                wintypes.UINT,
                ctypes.POINTER(ctypes.c_void_p),
                wintypes.DWORD,
            ]
            shell32.SHOpenFolderAndSelectItems.restype = ctypes.c_long

            # Initialize COM in apartment threaded mode if needed
            hr_init = ole32.CoInitializeEx(None, 2)  # COINIT_APARTMENTTHREADED
            need_uninit = hr_init in (0, 1)  # S_OK (0) or S_FALSE (1)

            try:
                pidl_file = ctypes.c_void_p()
                hr_file = shell32.SHParseDisplayName(
                    str(path), None, ctypes.byref(pidl_file), 0, None
                )

                pidl_parent = ctypes.c_void_p()
                hr_parent = shell32.SHParseDisplayName(
                    str(path.parent), None, ctypes.byref(pidl_parent), 0, None
                )

                if hr_file == 0 and hr_parent == 0 and pidl_file.value and pidl_parent.value:
                    child_pidl = shell32.ILFindLastID(pidl_file)
                    apidl = (ctypes.c_void_p * 1)(child_pidl)
                    hr_open = shell32.SHOpenFolderAndSelectItems(pidl_parent, 1, apidl, 0)

                    ole32.CoTaskMemFree(pidl_file)
                    ole32.CoTaskMemFree(pidl_parent)

                    if hr_open == 0:
                        return True
                else:
                    if pidl_file.value:
                        ole32.CoTaskMemFree(pidl_file)
                    if pidl_parent.value:
                        ole32.CoTaskMemFree(pidl_parent)
            finally:
                if need_uninit:
                    ole32.CoUninitialize()
        except Exception as exc:
            logger.debug("SHOpenFolderAndSelectItems failed: %s", exc)

        # Attempt 2: Fallback to explorer.exe /select,<path>
        try:
            subprocess.Popen(
                ["explorer.exe", f"/select,{path}"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception as exc:
            logger.warning("explorer.exe fallback failed: %s", exc)
            return False

    except Exception as exc:
        logger.warning("reveal_in_explorer unhandled exception: %s", exc)
        return False
