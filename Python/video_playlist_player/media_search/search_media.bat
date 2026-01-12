@echo off
chcp 65001 > nul
title Media Search V2 - HTML + VLC

REM =====================================================
REM CONFIGURAÇÃO
REM =====================================================

set PYTHON_EXE=python
set SCRIPT_PATH=C:\dev\scripts\ScriptsUteis\Python\video_playlist_player\media_search\media_search.py

set PATH_1=C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript
set PATH_2=C:\dev\scripts\ScriptsUteis\Python\Gemini\MakeVideoGemini\outputs\videos
set PATH_3=C:\Users\leand\Desktop\wordbank

REM =====================================================
REM EXECUÇÃO
REM =====================================================

%PYTHON_EXE% "%SCRIPT_PATH%" ^
"%PATH_1%" ^
"%PATH_2%" ^
"%PATH_3%"

pause
