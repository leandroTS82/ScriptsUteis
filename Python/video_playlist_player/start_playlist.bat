@echo off
title Video Playlist Player

REM ============================================
REM AJUSTE OS PARÂMETROS AQUI
REM ============================================

set VIDEO_PATH=C:\Users\leand\Desktop\wordbank
set REPEAT_VIDEO=2
set PAUSE_SECONDS=30
set SHUFFLE=--shuffle
set LOOP=--loop

REM ============================================

python video_playlist_player.py ^
 --path "%VIDEO_PATH%" ^
 --use-mapping ^
 --repeat-video %REPEAT_VIDEO% ^
 --pause %PAUSE_SECONDS% ^
 %SHUFFLE% ^
 %LOOP%

pause
