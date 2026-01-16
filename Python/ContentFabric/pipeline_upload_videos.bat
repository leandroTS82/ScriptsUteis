@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ============================================================
REM PIPELINE DE GERAÇÃO E UPLOAD DE VÍDEOS (RESILIENTE)
REM ============================================================

REM -------- LOG CONFIG --------
set LOG_DIR=C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\pipeline_upload_videos_Logs
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set RUN_TS=%%i
set LOG_FILE=%LOG_DIR%\pipeline_upload_%RUN_TS%.txt

REM -------- LOG START --------
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

set VIDEOS_DIR=C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\Videos
set GROQ_FAIL_DIR=C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\groq_MakeVideoFail

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

call :log [2/8] run_batch.py (MakeVideoGemini)

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
REM 4 - GROQ RESILIENT PIPELINE (4 PASSES)
REM ------------------------------------------------------------

if not exist "%GROQ_FAIL_DIR%" mkdir "%GROQ_FAIL_DIR%"

for %%P in (1 2 3 4) do (

    call :log ------------------------------------------------------------
    call :log [4/8] GROQ PASS %%P OF 4
    call :log ------------------------------------------------------------

    REM ---- GROQ MAKE VIDEO (NON-BLOCKING)
    pushd C:\dev\scripts\ScriptsUteis\Python\ContentFabric\4GroqIA
    python groq_MakeVideo.py "%VIDEOS_DIR%" >> "%LOG_FILE%" 2>&1
    if errorlevel 1 (
        call :log [WARN] groq_MakeVideo.py failed on pass %%P - continuing
    ) else (
        call :log [OK] groq_MakeVideo.py completed on pass %%P
    )
    popd

    REM ---- ENABLE TO YOUTUBE UPLOAD
    call :log [STEP] EnableToYoutubeUpload.py
    pushd C:\dev\scripts\ScriptsUteis\Python\ContentFabric\5youtube-upload
    python EnableToYoutubeUpload.py >> "%LOG_FILE%" 2>&1
    popd

    REM ---- CHECK REMAINING VIDEOS
    if exist "%VIDEOS_DIR%\*.mp4" (
        call :log [INFO] Videos still present - moving JSONs to groq_MakeVideoFail
        move "%VIDEOS_DIR%\*.json" "%GROQ_FAIL_DIR%" >nul 2>&1
    ) else (
        call :log [OK] No remaining videos after pass %%P
    )

    REM ---- SYNC JSONS
    call :log [STEP] sync_missing_jsons.py
    pushd C:\dev\scripts\ScriptsUteis\Python\ContentFabric\4GroqIA
    python sync_missing_jsons.py >> "%LOG_FILE%" 2>&1
    popd
)

REM ------------------------------------------------------------
REM 5 - FINAL CONSOLIDATION
REM ------------------------------------------------------------

call :log ------------------------------------------------------------
call :log [FINAL] EnableToYoutubeUpload.py
call :log ------------------------------------------------------------

pushd C:\dev\scripts\ScriptsUteis\Python\ContentFabric\5youtube-upload
python EnableToYoutubeUpload.py >> "%LOG_FILE%" 2>&1
popd

if exist "%VIDEOS_DIR%\*.mp4" (
    call :log [FINAL] Videos still present - moving JSONs to groq_MakeVideoFail
    move "%VIDEOS_DIR%\*.json" "%GROQ_FAIL_DIR%" >nul 2>&1
)

call :log [FINAL] sync_missing_jsons.py
pushd C:\dev\scripts\ScriptsUteis\Python\ContentFabric\4GroqIA
python sync_missing_jsons.py >> "%LOG_FILE%" 2>&1
popd

call :log [FINAL] EnableToYoutubeUpload.py
pushd C:\dev\scripts\ScriptsUteis\Python\ContentFabric\5youtube-upload
python EnableToYoutubeUpload.py >> "%LOG_FILE%" 2>&1
popd

REM ------------------------------------------------------------
REM 6 - COPY FILES SMART
REM ------------------------------------------------------------

call :log [8/8] 21-copy-files-smart.ps1
powershell -ExecutionPolicy Bypass -File C:\dev\scripts\ScriptsUteis\PowerShell\21-copy-files-smart.ps1 >> "%LOG_FILE%" 2>&1

call :log ============================================================
call :log PIPELINE COMPLETED WITH GROQ RESILIENCE
call :log LOG FILE: %LOG_FILE%
call :log ============================================================

exit /b 0

REM ------------------------------------------------------------
REM ERROR HANDLING
REM ------------------------------------------------------------

:error
call :log ============================================================
call :log PIPELINE FAILED
call :log Check log file: %LOG_FILE%
call :log ============================================================
pause
exit /b 1

REM ------------------------------------------------------------
REM LOG FUNCTION
REM ------------------------------------------------------------

:log
echo %*
echo %*>> "%LOG_FILE%"
exit /b
