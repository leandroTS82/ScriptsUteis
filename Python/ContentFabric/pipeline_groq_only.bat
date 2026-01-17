@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ============================================================
REM PIPELINE BASE — ETAPAS 1, 2 E 3
REM (Backup + MakeVideoGemini + MoveFiles)
REM ============================================================

REM -------- LOG CONFIG --------
set LOG_DIR=C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\pipeline_upload_videos_Logs
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set RUN_TS=%%i
set LOG_FILE=%LOG_DIR%\pipeline_base_%RUN_TS%.txt

REM -------- LOG START --------
call :log ============================================================
call :log PIPELINE BASE STARTED - %DATE% %TIME%
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

call :log [1/3] Backup CreateLater.json

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

call :log [2/3] run_batch.py (MakeVideoGemini)

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

call :log [3/3] Archive CreatedMovies + Move files

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
REM SUCCESS
REM ------------------------------------------------------------

call :log ============================================================
call :log PIPELINE BASE COMPLETED SUCCESSFULLY
call :log LOG FILE: %LOG_FILE%
call :log ============================================================

exit /b 0

REM ------------------------------------------------------------
REM ERROR HANDLING
REM ------------------------------------------------------------

:error
call :log ============================================================
call :log PIPELINE BASE FAILED
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
