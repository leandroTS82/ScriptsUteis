@echo off
title Video Playlist Player
chcp 65001 > nul

REM ==========================================================
REM 🎬 VIDEO PLAYLIST PLAYER - MENU PRINCIPAL
REM ==========================================================

REM ==========================================================
REM CONFIGURAÇÕES GERAIS
REM ==========================================================

REM Pasta onde as playlists inteligentes são geradas
set PLAYLIST_FOLDER=C:\Playlists\01-smart_playlists

REM Caminho do script Smart Playlist
set SMART_PLAYLIST_SCRIPT=C:\dev\scripts\ScriptsUteis\Python\video_playlist_player\build_smart_playlist.py


echo.
echo ==========================================================
echo 🎬 VIDEO PLAYLIST
echo ==========================================================
echo 1 - Build Smart Playlist (IA / filtros)
echo 2 - Player automático (subset / loop)
echo ==========================================================
echo.

set /p MODE=Escolha uma opção (1/2): 

if "%MODE%"=="1" goto SMART
if "%MODE%"=="2" goto PLAYER

echo ❌ Opção inválida
pause
exit /b


REM ==========================================================
REM ======================= OPÇÃO 1 ==========================
REM ===== BUILD SMART PLAYLIST + ABRIR PASTA =================
REM ==========================================================
:SMART
echo.
echo ▶ Executando Build Smart Playlist...
python "%SMART_PLAYLIST_SCRIPT%"

echo.
set /p OPEN_FOLDER=Deseja abrir a pasta de playlists agora? (s/n): 

if /I "%OPEN_FOLDER%"=="s" (
    echo ▶ Abrindo pasta de playlists...
    explorer "%PLAYLIST_FOLDER%"
)

pause
exit /b


REM ==========================================================
REM ======================= OPÇÃO 2 ==========================
REM ==========================================================
:PLAYER

REM ======================= CONFIGURAÇÕES ================================
set VIDEO_PATH=C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - LeandrinhoMovies
set REPEAT_VIDEO=1
set PAUSE_SECONDS=120

REM ======================= MODOS (true / false) =========================
set USE_MAPPING=true
set USE_RANDOM_SUBSET=true
set REUSE_LAST_SUBSET=false
set SUBSET_RESET_DAILY=false
set SUBSET_FIXED_SIZE=true
set SUBSET_MAX=10

REM ======================= CONTROLE DE TEMPO ============================
set ENABLE_MAX_PLAYTIME=true
set MAX_TOTAL_PLAYTIME_MINUTES=15

REM ======================= FLAGS DE EXECUÇÃO ============================
set SHUFFLE=true
set LOOP=true

REM ===================== PERGUNTA INTERATIVA ============================
echo.
set /p USER_CHOICE=Deseja reutilizar o ultimo subset salvo? (s/n): 

if /I "%USER_CHOICE%"=="s" (
    set REUSE_LAST_SUBSET=true
) else (
    set REUSE_LAST_SUBSET=false
)

REM =================== MONTAGEM DOS ARGUMENTOS ==========================
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

REM ============================ EXECUÇÃO ================================
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
exit /b
