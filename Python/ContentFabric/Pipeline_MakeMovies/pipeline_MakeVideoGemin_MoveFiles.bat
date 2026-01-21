@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ============================================================
REM PIPELINE BASE — ETAPAS 1, 2 E 3
REM (Backup + MakeVideoGemini + MoveFiles)
REM ============================================================

REM -------- PATHS PRINCIPAIS --------
set AI_HELPER_DIR=C:\dev\scripts\ScriptsUteis\Python\AI_EnglishHelper
set READY_PATH=C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\ReadyToBeCreated

set CREATE_LATER=%AI_HELPER_DIR%\CreateLater.json
set TEMP_BACKUP=%AI_HELPER_DIR%\temp_CreateLater.json
set CREATED_MOVIES_DIR=%AI_HELPER_DIR%\History_Created
set LOCK_FILE=%AI_HELPER_DIR%\pipeline.lock

set LOG_DIR=C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\pipeline_upload_videos_Logs
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set TS=%%i
set LOG_FILE=%LOG_DIR%\pipeline_base_%TS%.log

call :log PIPELINE STARTED

REM ------------------------------------------------------------
REM BACKUP CreateLater.json
REM ------------------------------------------------------------
if not exist "%CREATE_LATER%" goto :error
copy "%CREATE_LATER%" "%TEMP_BACKUP%" /Y >nul || goto :error

REM ------------------------------------------------------------
REM EXECUÇÃO MakeVideoGemini
REM ------------------------------------------------------------
pushd C:\dev\scripts\ScriptsUteis\Python\Gemini\MakeVideoGemini
python run_batch.py >> "%LOG_FILE%" 2>&1 || goto :error
popd

REM ------------------------------------------------------------
REM MOVE FILES
REM ------------------------------------------------------------
powershell -ExecutionPolicy Bypass -File C:\dev\scripts\ScriptsUteis\PowerShell\20-MoveFiles.ps1 >> "%LOG_FILE%" 2>&1 || goto :error

REM ------------------------------------------------------------
REM SUCCESS
REM ------------------------------------------------------------
for %%f in ("%READY_PATH%\processing_*.json") do ren "%%f" "success_%%~nxf"

del "%LOCK_FILE%" >nul 2>&1
call :log PIPELINE SUCCESS
exit /b 0

REM ------------------------------------------------------------
REM ERROR
REM ------------------------------------------------------------
:error
for %%f in ("%READY_PATH%\processing_*.json") do ren "%%f" "error_%%~nxf"

del "%LOCK_FILE%" >nul 2>&1
call :log PIPELINE ERROR
exit /b 1

REM ------------------------------------------------------------
REM LOG FUNCTION
REM ------------------------------------------------------------
:log
echo %*
echo %*>> "%LOG_FILE%"
exit /b
