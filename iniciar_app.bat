@echo off
setlocal
chcp 65001 >nul
title EVYDÊNCIA Print Generator

echo ======================================================================
echo   EVYDÊNCIA Print Generator — Iniciando Aplicação Desktop
echo ======================================================================
echo.

cd /d "%~dp0"

REM Compila o frontend se dist não existir
if not exist "apps\ui\dist\index.html" (
    echo [INFO] Build da interface não encontrado. Compilando interface...
    call npm --prefix apps\ui run build
    if errorlevel 1 (
        echo [ERRO] Falha ao compilar a interface web. Verifique o Node.js/npm.
        pause
        exit /b 1
    )
)

REM Executa a aplicação via virtualenv
if exist ".venv\Scripts\python.exe" (
    echo [INFO] Iniciando com ambiente virtual Python (.venv)...
    ".venv\Scripts\python.exe" -m evydencia_print_generator --gui %*
) else (
    echo [INFO] Iniciando com Python global...
    python -m evydencia_print_generator --gui %*
)

if errorlevel 1 (
    echo.
    echo [ERRO] A aplicação encerrou com código de erro %errorlevel%.
    pause
)

endlocal
