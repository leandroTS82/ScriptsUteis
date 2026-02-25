@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

set PIPELINE_DIR=C:\dev\scripts\ScriptsUteis\Python\ContentFabric\Pipeline_MakeMovies
set RUNTIME_DIR=%PIPELINE_DIR%\_runtime

set READY_PATH=C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Base\ReadyToBeCreated
set AI_HELPER_DIR=C:\dev\scripts\ScriptsUteis\Python\AI_EnglishHelper

set CREATE_LATER=%AI_HELPER_DIR%\CreateLater.json
set TEMP_BACKUP=%RUNTIME_DIR%\temp_CreateLater.json
set LOCK_FILE=%RUNTIME_DIR%\pipeline.lock

set LOG_ROOT=C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Base\pipeline_upload_videos_Logs
set RUN_ID=%1
set LOG_DIR=%LOG_ROOT%\%RUN_ID%
set LOG_FILE=%LOG_DIR%\pipeline.log

REM BACKUP
if not exist "%CREATE_LATER%" goto :error
copy "%CREATE_LATER%" "%TEMP_BACKUP%" /Y >nul || goto :error

REM MAKE VIDEO
pushd C:\dev\scripts\ScriptsUteis\Python\Gemini\MakeVideoGemini
python run_batch.py >>"%LOG_FILE%" 2>&1 || goto :error
popd

REM MOVE FILES
powershell -ExecutionPolicy Bypass -File C:\dev\scripts\ScriptsUteis\PowerShell\20-MoveFiles.ps1 >>"%LOG_FILE%" 2>&1 || goto :error

REM SUCCESS
for %%f in ("%READY_PATH%\processing_*.json") do ren "%%f" "success_%%~nxf"
del "%LOCK_FILE%" >nul 2>&1
exit /b 0

:error
for %%f in ("%READY_PATH%\processing_*.json") do ren "%%f" "error_%%~nxf"
del "%LOCK_FILE%" >nul 2>&1
exit /b 1
