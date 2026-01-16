@echo off
chcp 65001 > nul
title Gerador de Playlist por Data

REM ======================================================
REM CONFIGURAÇÕES (AJUSTE SOMENTE AQUI)
REM ======================================================

REM Caminho do Python (se já estiver no PATH, pode deixar apenas "python")
set PYTHON_EXE=python

REM Caminho do script Python
set SCRIPT_PATH=build_playlist_by_date.py

REM Intervalo de datas (dd/MM/yyyy)
set FROM_DATE=01/01/2026
set TO_DATE=16/01/2026

REM Diretório onde o .m3u será gerado
set OUTPUT_PATH=C:\Users\leand\Desktop\wordbank\playlists

REM ======================================================
REM EXECUÇÃO
REM ======================================================

echo ================================================
echo 🎬 GERANDO PLAYLIST POR INTERVALO DE DATA
echo ================================================
echo Script : %SCRIPT_PATH%
echo De     : %FROM_DATE%
echo Até    : %TO_DATE%
echo Saída  : %OUTPUT_PATH%
echo.

"%PYTHON_EXE%" "%SCRIPT_PATH%" ^
  --from-date "%FROM_DATE%" ^
  --to-date "%TO_DATE%" ^
  --output-path "%OUTPUT_PATH%"

echo.
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Erro ao gerar playlist
) else (
    echo ✅ Processo finalizado com sucesso
)

echo.
pause
