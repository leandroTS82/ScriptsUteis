@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ============================================================
REM PIPELINE DE GERAÇÃO E UPLOAD DE VÍDEOS
REM ============================================================

REM -------- LOG CONFIG --------
set LOG_DIR=C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\pipeline_upload_videos_Logs
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set RUN_TS=%%i
set LOG_FILE=%LOG_DIR%\pipeline_upload_%RUN_TS%.txt

REM -------- LOG FUNCTION --------
call :log ============================================================
call :log PIPELINE STARTED - %DATE% %TIME%
call :log ============================================================

REM ------------------------------------------------------------
REM PATHS
REM ------------------------------------------------------------

set AI_HELPER_DIR=C:\dev\scripts\ScriptsUteis\Python\AI_EnglishHelper
set CREATE_LATER=%AI_HELPER_DIR%\CreateLater.json
set TEMP_BACKUP=%AI_HELPER_DIR%\temp_CreateLater.json
set CREATED_MOVIES_DIR=%AI_HELPER_DIR%\History_Created

REM ------------------------------------------------------------
REM 1 - BACKUP CreateLater.json
REM ------------------------------------------------------------

call :log [1/8] Backup CreateLater.json

if not exist "%CREATE_LATER%" (
    call :log [ERROR] CreateLater.json not found
    goto :error
)

copy "%CREATE_LATER%" "%TEMP_BACKUP%" /Y >nul
if errorlevel 1 (
    call :log [ERROR] Backup failed
    goto :error
)

call :log [OK] Backup created

REM ------------------------------------------------------------
REM 2 - RUN MakeVideoGemini
REM ------------------------------------------------------------

call :log [2/8] run_batch.py

pushd C:\dev\scripts\ScriptsUteis\Python\Gemini\MakeVideoGemini
python run_batch.py >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    popd
    call :log [ERROR] run_batch.py failed
    goto :error
)
popd

call :log [OK] Videos generated

REM ------------------------------------------------------------
REM 3 - ARCHIVE JSON + MOVE FILES
REM ------------------------------------------------------------

call :log [3/8] Archive CreatedMovies + Move files

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMddHHmm"') do set TS=%%i
if not exist "%CREATED_MOVIES_DIR%" mkdir "%CREATED_MOVIES_DIR%"

move "%TEMP_BACKUP%" "%CREATED_MOVIES_DIR%\%TS%_CreatedMovies.json" >nul
if errorlevel 1 (
    call :log [ERROR] Failed to archive CreatedMovies
    goto :error
)

powershell -ExecutionPolicy Bypass -File C:\dev\scripts\ScriptsUteis\PowerShell\20-MoveFiles.ps1 >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    call :log [ERROR] 20-MoveFiles.ps1 failed
    goto :error
)

call :log [OK] Files moved

REM ------------------------------------------------------------
REM 4 - GROQ MakeVideo (1ª PASSAGEM)
REM ------------------------------------------------------------

call :log [4/8] groq_MakeVideo.py (1st pass)

pushd C:\dev\scripts\ScriptsUteis\Python\ContentFabric\4GroqIA
python groq_MakeVideo.py "C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\Videos" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    popd
    call :log [ERROR] groq_MakeVideo.py failed (1st)
    goto :error
)
popd

call :log [OK] Groq 1st pass completed

REM ------------------------------------------------------------
REM 5 - ENABLE TO YOUTUBE UPLOAD
REM ------------------------------------------------------------

call :log [5/8] EnableToYoutubeUpload.py

pushd C:\dev\scripts\ScriptsUteis\Python\ContentFabric\5youtube-upload
python EnableToYoutubeUpload.py >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    popd
    call :log [ERROR] EnableToYoutubeUpload failed
    goto :error
)
popd

call :log [OK] Upload enabled

REM ------------------------------------------------------------
REM 6 - SYNC MISSING JSONs
REM ------------------------------------------------------------

call :log [6/8] sync_missing_jsons.py

pushd C:\dev\scripts\ScriptsUteis\Python\ContentFabric\4GroqIA
python sync_missing_jsons.py >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    popd
    call :log [ERROR] sync_missing_jsons failed
    goto :error
)
popd

call :log [OK] JSONs synced

REM ------------------------------------------------------------
REM 7 - GROQ + ENABLE (2ª PASSAGEM)
REM ------------------------------------------------------------

call :log [7/8] Groq + Enable (2nd pass)

pushd C:\dev\scripts\ScriptsUteis\Python\ContentFabric\4GroqIA
python groq_MakeVideo.py "C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\Videos" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    popd
    call :log [ERROR] groq_MakeVideo.py failed (2nd)
    goto :error
)
popd

pushd C:\dev\scripts\ScriptsUteis\Python\ContentFabric\5youtube-upload
python EnableToYoutubeUpload.py >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    popd
    call :log [ERROR] EnableToYoutubeUpload failed (2nd)
    goto :error
)
popd

call :log [OK] Second pass completed

REM ------------------------------------------------------------
REM 8 - COPY FILES SMART
REM ------------------------------------------------------------

call :log [8/8] 21-copy-files-smart.ps1

powershell -ExecutionPolicy Bypass -File C:\dev\scripts\ScriptsUteis\PowerShell\21-copy-files-smart.ps1 >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    call :log [ERROR] 21-copy-files-smart.ps1 failed
    goto :error
)

call :log [OK] Copy Files Smart completed

call :log ============================================================
call :log PIPELINE COMPLETED SUCCESSFULLY
call :log LOG FILE: %LOG_FILE%
call :log ============================================================

exit /b 0

:error
call :log ============================================================
call :log PIPELINE FAILED
call :log Check log file: %LOG_FILE%
call :log ============================================================
pause
exit /b 1

REM -------- LOG FUNCTION --------
:log
echo %*
echo %*>> "%LOG_FILE%"
exit /b
