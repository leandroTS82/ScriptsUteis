@echo off
title Video Playlist Player
chcp 65001 > nul

REM =====================================================
REM =============== CONFIGURAÇÕES =======================
REM =====================================================

REM Caminho dos vídeos
set VIDEO_PATH=C:\Users\leand\Desktop\wordbank

REM Quantas vezes cada vídeo deve ser reproduzido
set REPEAT_VIDEO=2

REM Pausa entre execuções (em segundos)
set PAUSE_SECONDS=30

REM -----------------------------------------------------
REM MODOS (true / false)
REM -----------------------------------------------------

REM Ativar controle por JSON (contador e balanceamento)
set USE_MAPPING=true

REM Ativar seleção de subconjunto aleatório de vídeos
set USE_RANDOM_SUBSET=true

REM Quantidade MÁXIMA de vídeos no subconjunto
set SUBSET_MAX=5

REM -----------------------------------------------------
REM FLAGS DE EXECUÇÃO
REM -----------------------------------------------------

REM Embaralhar vídeos
set SHUFFLE=true

REM Repetir playlist infinitamente
set LOOP=true

REM =====================================================
REM ============= MONTAGEM DOS ARGUMENTOS ===============
REM =====================================================

set ARGS=--path "%VIDEO_PATH%"

REM repeat e pausa
set ARGS=%ARGS% --repeat-video %REPEAT_VIDEO%
set ARGS=%ARGS% --pause %PAUSE_SECONDS%

REM mapping
if /I "%USE_MAPPING%"=="true" (
    set ARGS=%ARGS% --use-mapping
)

REM random subset
if /I "%USE_RANDOM_SUBSET%"=="true" (
    set ARGS=%ARGS% --use-random-subset --subset-max %SUBSET_MAX%
)

REM shuffle
if /I "%SHUFFLE%"=="true" (
    set ARGS=%ARGS% --shuffle
)

REM loop
if /I "%LOOP%"=="true" (
    set ARGS=%ARGS% --loop
)

REM =====================================================
REM ================= EXECUÇÃO ==========================
REM =====================================================

echo.
echo ▶ Iniciando Video Playlist Player
echo ▶ Caminho: %VIDEO_PATH%
echo ▶ Parâmetros: %ARGS%
echo.

python video_playlist_player.py %ARGS%

echo.
echo ✔ Execução finalizada
pause
