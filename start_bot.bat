@echo off
title ALM Chatbot - Leo
cd /d "%~dp0alm_bot"

echo 🦁 ALM Chatbot - %AGENCY_NAME%
echo ================================
echo.

REM Verificar si existe .env
if not exist .env (
    echo [!] No hay archivo .env
    echo    Copiando desde .env.example...
    copy .env.example .env > nul
    echo    IMPORTANTE: Editá alm_bot/.env con tus credenciales
    echo.
)

REM Verificar dependencias
echo [*] Verificando dependencias...
pip install -r requirements.txt -q
echo.

echo [*] Iniciando servidor...
echo    http://localhost:8000
echo    http://localhost:8000/health
echo    http://localhost:8000/docs
echo.
echo    Para salir: Ctrl+C
echo ================================
echo.

python main.py
pause
