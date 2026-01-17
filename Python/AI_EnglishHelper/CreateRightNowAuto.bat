@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul

echo ==================================================
echo [START] Hourly Pipeline - %DATE% %TIME%
echo ==================================================

REM --------------------------------------------------
REM CONFIGURAÇÕES
REM --------------------------------------------------

set PYTHON_EXE=python

set SCRIPT_READY=C:\dev\scripts\ScriptsUteis\Python\AI_EnglishHelper\GetReadyToBeCreated.py
set SCRIPT_PIPELINE=C:\dev\scripts\ScriptsUteis\Python\ContentFabric\pipeline_groq_only.bat

REM --------------------------------------------------
REM EXECUÇÃO 1 - Python
REM --------------------------------------------------

echo [INFO] Executando GetReadyToBeCreated.py
"%PYTHON_EXE%" "%SCRIPT_READY%"

if errorlevel 1 (
    echo [ERROR] Falha ao executar GetReadyToBeCreated.py
    goto :end
)

echo [OK] GetReadyToBeCreated.py finalizado com sucesso

REM --------------------------------------------------
REM EXECUÇÃO 2 - Pipeline BAT
REM --------------------------------------------------

echo [INFO] Executando pipeline_groq_only.bat
call "%SCRIPT_PIPELINE%"

if errorlevel 1 (
    echo [ERROR] Falha ao executar pipeline_groq_only.bat
    goto :end
)

echo [OK] pipeline_groq_only.bat finalizado com sucesso

:end
echo ==================================================
echo [END] Pipeline finalizado - %DATE% %TIME%
echo ==================================================

endlocal
exit /b 0
