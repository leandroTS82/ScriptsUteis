@echo off
setlocal
chcp 65001 >nul

REM ==================================================
REM ORQUESTRADOR PRINCIPAL (SILENCIOSO)
REM ==================================================

set PYTHON_EXE=C:\Python311\python.exe
set BASE_DIR=C:\dev\scripts\ScriptsUteis\Python\AI_EnglishHelper

set SCRIPT_READY=%BASE_DIR%\GetReadyToBeCreated.py
set SCRIPT_PIPELINE=C:\dev\scripts\ScriptsUteis\Python\ContentFabric\pipeline_MakeVideoGemin_MoveFiles.bat

set LOG_DIR=C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\pipeline_upload_videos_Logs
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set TS=%%i
set LOG_FILE=%LOG_DIR%\orchestrator_%TS%.log

echo [START] %DATE% %TIME%>>"%LOG_FILE%"

"%PYTHON_EXE%" "%SCRIPT_READY%" >>"%LOG_FILE%" 2>&1
set READY_EXIT=%ERRORLEVEL%

if %READY_EXIT%==0 (
    echo [INFO] NOOP – nada a processar>>"%LOG_FILE%"
    goto :end
)

if %READY_EXIT%==1 (
    echo [ERROR] Falha no gatekeeper>>"%LOG_FILE%"
    goto :end
)

if %READY_EXIT%==2 (
    echo [OK] Dados preparados – iniciando pipeline>>"%LOG_FILE%"
) else (
    echo [ERROR] Exit code inesperado %READY_EXIT%>>"%LOG_FILE%"
    goto :end
)

call "%SCRIPT_PIPELINE%" >>"%LOG_FILE%" 2>&1

:end
echo [END] %DATE% %TIME%>>"%LOG_FILE%"
exit /b 0
