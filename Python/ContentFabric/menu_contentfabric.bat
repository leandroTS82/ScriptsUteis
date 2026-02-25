@echo off
chcp 65001 >nul
setlocal

:: ==================================================
:: MENU PRINCIPAL (ABAS)
:: ==================================================
:MENU
cls
echo ==================================================
echo            CONTENT FABRIC
echo ==================================================
echo.
echo  1 - Criacao de Conteudo
echo  2 - Sanitizacao (Pre-Youtube)
echo  3 - Publicacao (YouTube)
echo  4 - Distribuicao / Consumo
echo.
echo  s - Sair
echo.
set /p OP=Escolha a aba: 

if "%OP%"=="1" goto CRIACAO
if "%OP%"=="2" goto SANITIZACAO
if "%OP%"=="3" goto PUBLICACAO
if "%OP%"=="4" goto DISTRIBUICAO
if /i "%OP%"=="s" goto SAIR

goto MENU


:: ==================================================
:: ABA 1 - CRIACAO
:: ==================================================
:CRIACAO
cls
echo ==================================================
echo        ABA - CRIACAO DE CONTEUDO
echo ==================================================
echo.
echo  1 - Consolidar BaseTerms (Preparar novos conteudos)
echo  2 - Criar Videos (Leandrinho)
echo  3 - Mover arquivos para Sanitizacao
echo.
echo  '0' - Voltar
echo.
set /p OP=Escolha: 

if "%OP%"=="1" goto OP12
if "%OP%"=="2" goto OP11
if "%OP%"=="3" goto OP5
if /i "%OP%"=="0" goto MENU

goto CRIACAO


:: ==================================================
:: ABA 2 - SANITIZACAO
:: ==================================================
:SANITIZACAO
cls
echo ==================================================
echo        ABA - SANITIZACAO (PRE-YOUTUBE)
echo ==================================================
echo.
echo  1 - Listar Videos na pasta de sanitizacao
echo  2 - Sincronizar JSONs faltantes
echo  3 - Limpar filmes processados
echo  4 - Corrigir JSON (tag)
echo  5 - Ajustar contrato YouTube (Groq)
echo  6 - Mover videos longos + limpar history
echo  7 - Excluir videos manualmente + gerar pending
echo.
echo  '0' - Voltar
echo.
set /p OP=Escolha: 

if "%OP%"=="1" goto OP9
if "%OP%"=="2" goto OP3
if "%OP%"=="3" goto OP4
if "%OP%"=="4" goto OP10
if "%OP%"=="5" goto OP1
if "%OP%"=="6" goto OP13
if "%OP%"=="7" goto OP14
if /i "%OP%"=="0" goto MENU

goto SANITIZACAO


:: ==================================================
:: ABA 3 - PUBLICACAO
:: ==================================================
:PUBLICACAO
cls
echo ==================================================
echo        ABA - PUBLICACAO (YOUTUBE)
echo ==================================================
echo.
echo  1 - Upload para YouTube
echo.
echo  '0' - Voltar
echo.
set /p OP=Escolha: 

if "%OP%"=="1" goto OP2
if /i "%OP%"=="0" goto MENU

goto PUBLICACAO


:: ==================================================
:: ABA 4 - DISTRIBUICAO
:: ==================================================
:DISTRIBUICAO
cls
echo ==================================================
echo        ABA - DISTRIBUICAO / CONSUMO
echo ==================================================
echo.
echo  1 - Copiar arquivos inteligente
echo  2 - Sync Wordbank + JSONs (zip)
echo  3 - Sync Audios para ZIP
echo.
echo  '0' - Voltar
echo.
set /p OP=Escolha: 

if "%OP%"=="1" goto OP6
if "%OP%"=="2" goto OP7
if "%OP%"=="3" goto OP8
if /i "%OP%"=="0" goto MENU

goto DISTRIBUICAO


:: ==================================================
:: EXECUCOES
:: ==================================================

:OP1
cd /d "C:\dev\scripts\ScriptsUteis\Python\ContentFabric\4GroqIA"
python groq_MakeVideo.py "C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\Videos"
pause
goto SANITIZACAO

:OP2
cd /d "C:\dev\scripts\ScriptsUteis\Python\ContentFabric\5youtube-upload"
python EnableToYoutubeUpload.py
pause
goto PUBLICACAO

:OP3
cd /d "C:\dev\scripts\ScriptsUteis\Python\ContentFabric\4GroqIA"
python sync_missing_jsons.py
pause
goto SANITIZACAO

:OP4
cd /d "C:\dev\scripts\ScriptsUteis\Python\ContentFabric\4GroqIA"
python cleanup_movies_processed.py
pause
goto SANITIZACAO

:OP5
cd /d "C:\dev\scripts\ScriptsUteis\Python\ContentFabric"
python run_move_files_mappings.py
pause
goto CRIACAO

:OP6
cd /d "C:\dev\scripts\ScriptsUteis\Python\ContentFabric"
python run_copy_files_smart.py
pause
goto DISTRIBUICAO

:OP7
cd /d "C:\dev\scripts\ScriptsUteis\Python\ContentFabric\0-TransfereArquivos"
python sync_wordbank_and_jsons.py
pause
goto DISTRIBUICAO

:OP8
cd /d "C:\dev\scripts\ScriptsUteis\Python\ContentFabric\0-TransfereArquivos"
python sync_audios_to_zip.py
pause
goto DISTRIBUICAO

:OP9
cd /d "C:\dev\scripts\ScriptsUteis\Python\ContentFabric"
python list_videos_directory.py
pause
goto SANITIZACAO

:OP10
cd /d "C:\dev\scripts\ScriptsUteis\Python\ContentFabric"
python fix_video_json_tags.py
pause
goto SANITIZACAO

:OP11
cd /d "C:\dev\scripts\ScriptsUteis\Python\Gemini\MakeVideoGemini"
python run_batch.py
pause
goto CRIACAO

:OP12
cd /d "C:\dev\scripts\ScriptsUteis\Python\EKF_EnglishKnowledgeFramework"
python consolidate_base_terms.py
pause
goto CRIACAO

:OP13
cd /d "C:\dev\scripts\ScriptsUteis\Python\ContentFabric"
python move_long_videos_and_clean_history.py
pause
goto SANITIZACAO

:OP14
cd /d "C:\dev\scripts\ScriptsUteis\Python\ContentFabric"
python delete_selected_videos_and_generate_pending.py
pause
goto SANITIZACAO


:SAIR
echo.
echo Encerrando menu...
timeout /t 1 >nul
exit
