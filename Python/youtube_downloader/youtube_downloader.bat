@echo off
chcp 65001 >nul
setlocal

echo ==============================================
echo  YOUTUBE DOWNLOADER - MP4 ALTA QUALIDADE
echo ==============================================

REM Ajuste o caminho se necessário
set SCRIPT_PATH=youtube_downloader.py

python "%SCRIPT_PATH%"

echo.
echo Pressione qualquer tecla para sair...
pause >nul
