@echo off
chcp 65001 >nul
setlocal

:MENU
cls
echo ==================================================
echo            CONTENT FABRIC - MENU
echo ==================================================
echo.

echo ================================
echo  FASE 1 - CRIACAO DE CONTEUDO
echo ================================
echo  12 - Consolidar BaseTerms (Preparar novos conteudos)
echo  11 - Criar Videos (Leandrinho)
echo   5 - Mover arquivos para Sanitizacao
echo.

echo ================================
echo  FASE 2 - SANITIZACAO (Pre-Youtube)
echo ================================
echo   9 - Listar Videos na pasta de sanitizacao
echo   3 - Sincronizar JSONs faltantes
echo   4 - Limpar filmes processados
echo  10 - Corrigir JSON (tag)
echo   1 - Ajustar contrato YouTube (Groq)
echo.

echo ================================
echo  FASE 3 - PUBLICACAO
echo ================================
echo   2 - Upload para YouTube
echo.

echo ================================
echo  FASE 4 - DISTRIBUICAO
echo ================================
echo   6 - Copiar arquivos inteligente
echo   7 - Sync Wordbank + JSONs (zip)
echo   8 - Sync Audios para ZIP
echo.

echo  Digite o numero da opcao
echo  ou digite "s" para sair
echo.
set /p OPCAO=Escolha: 

if /i "%OPCAO%"=="s" goto SAIR

REM 
if "%OPCAO%"=="12" goto OP12
if "%OPCAO%"=="11" goto OP11
if "%OPCAO%"=="10" goto OP10
if "%OPCAO%"=="9"  goto OP9
if "%OPCAO%"=="8"  goto OP8
if "%OPCAO%"=="7"  goto OP7
if "%OPCAO%"=="6"  goto OP6
if "%OPCAO%"=="5"  goto OP5
if "%OPCAO%"=="4"  goto OP4
if "%OPCAO%"=="3"  goto OP3
if "%OPCAO%"=="2"  goto OP2
if "%OPCAO%"=="1"  goto OP1

echo.
echo Opcao invalida.
pause
goto MENU

:OP1
cd /d "C:\dev\scripts\ScriptsUteis\Python\ContentFabric\4GroqIA"
python groq_MakeVideo.py "C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\Videos"
pause
goto MENU

:OP2
cd /d "C:\dev\scripts\ScriptsUteis\Python\ContentFabric\5youtube-upload"
python EnableToYoutubeUpload.py
pause
goto MENU

:OP3
cd /d "C:\dev\scripts\ScriptsUteis\Python\ContentFabric\4GroqIA"
python sync_missing_jsons.py
pause
goto MENU

:OP4
cd /d "C:\dev\scripts\ScriptsUteis\Python\ContentFabric\4GroqIA"
python cleanup_movies_processed.py
pause
goto MENU

:OP5
cd /d "C:\dev\scripts\ScriptsUteis\Python\ContentFabric"
python run_move_files_mappings.py
pause
goto MENU

:OP6
cd /d "C:\dev\scripts\ScriptsUteis\Python\ContentFabric"
python run_copy_files_smart.py
pause
goto MENU

:OP7
cd /d "C:\dev\scripts\ScriptsUteis\Python\ContentFabric\0-TransfereArquivos"
python sync_wordbank_and_jsons.py
pause
goto MENU

:OP8
cd /d "C:\dev\scripts\ScriptsUteis\Python\ContentFabric\0-TransfereArquivos"
python sync_audios_to_zip.py
pause
goto MENU

:OP9
cd /d "C:\dev\scripts\ScriptsUteis\Python\ContentFabric"
python list_videos_directory.py
pause
goto MENU

:OP10
cd /d "C:\dev\scripts\ScriptsUteis\Python\ContentFabric"
python fix_video_json_tags.py
pause
goto MENU

:OP11
cd /d "C:\dev\scripts\ScriptsUteis\Python\Gemini\MakeVideoGemini"
python run_batch.py
pause
goto MENU

:OP12
cd /d "C:\dev\scripts\ScriptsUteis\Python\EKF_EnglishKnowledgeFramework"
python consolidate_base_terms.py
pause
goto MENU


:SAIR
echo.
echo Encerrando menu...
timeout /t 1 >nul
exit