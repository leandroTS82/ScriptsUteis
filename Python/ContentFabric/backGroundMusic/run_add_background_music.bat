@echo off
chcp 65001 > nul
title 🎧 Mixagem de Áudio - Background Music

echo.
echo ===============================================
echo 🎧 Iniciando mixagem de áudios com fundo musical
echo ===============================================
echo.

REM === Ajuste o caminho do Python se necessário ===
set PYTHON_EXE=C:\Users\leand\AppData\Local\Programs\Python\Python313\python.exe

REM === Caminho do script ===
set SCRIPT_PATH=C:\dev\scripts\ScriptsUteis\Python\ContentFabric\backGroundMusic\add_background_musicy.py

REM === Valida Python ===
if not exist "%PYTHON_EXE%" (
    echo ❌ Python não encontrado:
    echo %PYTHON_EXE%
    pause
    exit /b 1
)

REM === Valida script ===
if not exist "%SCRIPT_PATH%" (
    echo ❌ Script não encontrado:
    echo %SCRIPT_PATH%
    pause
    exit /b 1
)

echo ▶ Executando script...
echo.

"%PYTHON_EXE%" "%SCRIPT_PATH%"

echo.
echo ===============================================
echo ✅ Processamento finalizado
echo ===============================================
echo.
pause
