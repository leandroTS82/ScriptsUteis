@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

REM ==================================================
REM ORQUESTRADOR PRINCIPAL (TOTALMENTE SILENCIOSO)
REM ==================================================

set PYTHON_EXE=python
set PIPELINE_DIR=C:\dev\scripts\ScriptsUteis\Python\ContentFabric\Pipeline_MakeMovies
set RUNTIME_DIR=%PIPELINE_DIR%\_runtime

set SCRIPT_READY=%PIPELINE_DIR%\GetReadyToBeCreated.py
set SCRIPT_PIPELINE=%PIPELINE_DIR%\pipeline_MakeVideoGemin_MoveFiles.bat

set LOG_ROOT=C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Base\pipeline_upload_videos_Logs

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMddHHmm"') do set RUN_ID=%%i
set LOG_DIR=%LOG_ROOT%\%RUN_ID%
mkdir "%LOG_DIR%" >nul 2>&1

set LOG_FILE=%LOG_DIR%\orchestrator.log

"%PYTHON_EXE%" "%SCRIPT_READY%" "%RUN_ID%" >>"%LOG_FILE%" 2>&1
set READY_EXIT=%ERRORLEVEL%

if "!READY_EXIT!"=="2" (
    echo [%DATE% %TIME%] Gatekeeper liberou pipeline >>"%LOG_FILE%"
    call "%SCRIPT_PIPELINE%" "%RUN_ID%" >>"%LOG_FILE%" 2>&1
) else (
    echo [%DATE% %TIME%] Gatekeeper bloqueou pipeline (exit=!READY_EXIT!) >>"%LOG_FILE%"
)

exit /b 0