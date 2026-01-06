@echo off
title Video Playlist Player
chcp 65001 > nul

REM =====================================================================
REM  VIDEO PLAYLIST PLAYER - ARQUIVO DE INICIALIZAÇÃO
REM
REM  Este arquivo executa o script:
REM      video_playlist_player.py
REM
REM  Ele permite controlar:
REM   - Caminho dos vídeos
REM   - Repetições
REM   - Pausa entre vídeos
REM   - Embaralhamento (shuffle)
REM   - Loop infinito
REM   - Controle inteligente por JSON (balanceamento)
REM   - Seleção de subconjunto aleatório de vídeos
REM
REM  IMPORTANTE:
REM   - Ajuste SOMENTE a seção "CONFIGURAÇÕES"
REM   - Não é necessário editar o script Python
REM =====================================================================


REM =====================================================================
REM ======================= CONFIGURAÇÕES ================================
REM =====================================================================

REM Caminho absoluto da pasta onde estão os vídeos
REM Exemplo:
REM   C:\Videos
REM   C:\Users\leand\Desktop\wordbank
set VIDEO_PATH=C:\Users\leand\Desktop\wordbank


REM Quantas vezes CADA vídeo será reproduzido
REM Exemplo:
REM   1 = toca uma vez
REM   2 = toca duas vezes antes de passar para o próximo
set REPEAT_VIDEO=2


REM Tempo de pausa ENTRE execuções (em segundos)
REM Exemplo:
REM   0  = sem pausa
REM   30 = aguarda 30 segundos entre vídeos
set PAUSE_SECONDS=30


REM =====================================================================
REM ======================= MODOS (true / false) =========================
REM =====================================================================

REM Ativa controle por JSON (video_play_count.json)
REM - Mantém histórico de quantas vezes cada vídeo tocou
REM - Prioriza vídeos menos reproduzidos
REM true  = ativado
REM false = desativado
set USE_MAPPING=true


REM Ativa seleção de um SUBCONJUNTO de vídeos
REM - Seleciona alguns vídeos e toca APENAS eles
REM - O conjunto é salvo em: selected_videos.json
REM - A seleção respeita os menos reproduzidos
REM
REM OBS: Este modo REQUER USE_MAPPING=true
set USE_RANDOM_SUBSET=true


REM Quantidade MÁXIMA de vídeos no subconjunto
REM Exemplo:
REM   5 = seleciona de 1 até 5 vídeos
REM   10 = seleciona de 1 até 10 vídeos
set SUBSET_MAX=5


REM =====================================================================
REM ======================= FLAGS DE EXECUÇÃO ============================
REM =====================================================================

REM Embaralha vídeos
REM true  = ordem aleatória
REM false = ordem controlada / natural
set SHUFFLE=true


REM Repetir a playlist indefinidamente
REM true  = loop infinito
REM false = executa uma vez e encerra
set LOOP=true


REM =====================================================================
REM =================== MONTAGEM DOS ARGUMENTOS ==========================
REM =====================================================================

REM NÃO ALTERE ESTA SEÇÃO
REM Ela apenas converte as opções acima em parâmetros do Python

set ARGS=--path "%VIDEO_PATH%"

REM Repetições e pausa
set ARGS=%ARGS% --repeat-video %REPEAT_VIDEO%
set ARGS=%ARGS% --pause %PAUSE_SECONDS%

REM Controle por JSON
if /I "%USE_MAPPING%"=="true" (
    set ARGS=%ARGS% --use-mapping
)

REM Subconjunto aleatório
if /I "%USE_RANDOM_SUBSET%"=="true" (
    set ARGS=%ARGS% --use-random-subset --subset-max %SUBSET_MAX%
)

REM Shuffle
if /I "%SHUFFLE%"=="true" (
    set ARGS=%ARGS% --shuffle
)

REM Loop
if /I "%LOOP%"=="true" (
    set ARGS=%ARGS% --loop
)


REM =====================================================================
REM ============================ EXECUÇÃO ================================
REM =====================================================================

echo.
echo ==========================================================
echo ▶ Iniciando Video Playlist Player
echo ▶ Pasta de vídeos: %VIDEO_PATH%
echo ▶ Parâmetros ativos:
echo    %ARGS%
echo ==========================================================
echo.

python video_playlist_player.py %ARGS%

echo.
echo ==========================================================
echo ✔ Execução finalizada
echo ==========================================================
pause
