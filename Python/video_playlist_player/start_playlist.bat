@echo off
title Video Playlist Player
chcp 65001 > nul

REM =====================================================================
REM  VIDEO PLAYLIST PLAYER - ARQUIVO DE INICIALIZAÇÃO
REM
REM  Ajuste SOMENTE a seção CONFIGURAÇÕES
REM =====================================================================


REM =====================================================================
REM ======================= CONFIGURAÇÕES ================================
REM =====================================================================

REM Caminho da pasta de vídeos
set VIDEO_PATH=C:\Users\leand\Desktop\wordbank

REM Quantas vezes cada vídeo será reproduzido
set REPEAT_VIDEO=2

REM Pausa entre execuções (segundos)
set PAUSE_SECONDS=60


REM =====================================================================
REM ======================= MODOS (true / false) =========================
REM =====================================================================

REM Controle por JSON (balanceamento)
set USE_MAPPING=true

REM Subconjunto aleatório
set USE_RANDOM_SUBSET=true

REM Reutilizar o último subset salvo (selected_videos.json)
set REUSE_LAST_SUBSET=false

REM Resetar subset diariamente
set SUBSET_RESET_DAILY=false

REM Subset com tamanho fixo (exatamente SUBSET_MAX)
set SUBSET_FIXED_SIZE=true

REM Quantidade máxima de vídeos no subset
set SUBSET_MAX=5


REM =====================================================================
REM ======================= CONTROLE DE TEMPO ============================
REM =====================================================================

REM Ativar tempo máximo total de execução
set ENABLE_MAX_PLAYTIME=true

REM Tempo máximo TOTAL em MINUTOS
set MAX_TOTAL_PLAYTIME_MINUTES=10


REM =====================================================================
REM ======================= FLAGS DE EXECUÇÃO ============================
REM =====================================================================

REM Embaralhar vídeos
set SHUFFLE=true

REM Loop infinito
set LOOP=true


REM =====================================================================
REM ===================== PERGUNTA INTERATIVA ============================
REM =====================================================================

echo.
set /p USER_CHOICE=Deseja reutilizar o ultimo subset salvo? (s/n): 

if /I "%USER_CHOICE%"=="s" (
    set REUSE_LAST_SUBSET=true
) else (
    set REUSE_LAST_SUBSET=false
)


REM =====================================================================
REM =================== MONTAGEM DOS ARGUMENTOS ==========================
REM =====================================================================

set ARGS=--path "%VIDEO_PATH%"
set ARGS=%ARGS% --repeat-video %REPEAT_VIDEO%
set ARGS=%ARGS% --pause %PAUSE_SECONDS%

if /I "%USE_MAPPING%"=="true" (
    set ARGS=%ARGS% --use-mapping
)

if /I "%USE_RANDOM_SUBSET%"=="true" (
    set ARGS=%ARGS% --use-random-subset --subset-max %SUBSET_MAX%
)

if /I "%REUSE_LAST_SUBSET%"=="true" (
    set ARGS=%ARGS% --reuse-last-subset
)

if /I "%SUBSET_RESET_DAILY%"=="true" (
    set ARGS=%ARGS% --subset-reset-daily
)

if /I "%SUBSET_FIXED_SIZE%"=="true" (
    set ARGS=%ARGS% --subset-fixed-size
)

if /I "%ENABLE_MAX_PLAYTIME%"=="true" (
    set ARGS=%ARGS% --enable-max-total-playtime --max-total-playtime-minutes %MAX_TOTAL_PLAYTIME_MINUTES%
)

if /I "%SHUFFLE%"=="true" (
    set ARGS=%ARGS% --shuffle
)

if /I "%LOOP%"=="true" (
    set ARGS=%ARGS% --loop
)


REM =====================================================================
REM ============================ EXECUÇÃO ================================
REM =====================================================================

echo.
echo ==========================================================
echo ▶ Video Playlist Player
echo ▶ Pasta: %VIDEO_PATH%
echo ▶ Parâmetros:
echo    %ARGS%
echo ==========================================================
echo.

python video_playlist_player.py %ARGS%

echo.
echo ==========================================================
echo ✔ Execução finalizada
echo ==========================================================
pause
