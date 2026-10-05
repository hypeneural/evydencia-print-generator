@echo off
setlocal
chcp 65001 >nul
title EVYDÊNCIA Print Generator — Servidor de Desenvolvimento Web

echo ======================================================================
echo   EVYDÊNCIA Print Generator — Servidor Web Vite (Modo Desenvolvimento)
echo ======================================================================
echo.

cd /d "%~dp0apps\ui"

echo [INFO] Iniciando Vite dev server...
echo [INFO] Acesse: http://localhost:5173
echo.
call npm run dev

endlocal
