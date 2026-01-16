@echo off
chcp 65001 > nul
title TranscriptV2 Runner

echo ==============================================
echo  TranscriptV2 - Execucao Interativa
echo ==============================================
echo.

REM ------------------------------------------------
REM CONFIGURACAO DO SCRIPT PYTHON
REM ------------------------------------------------
set PYTHON_SCRIPT=C:\dev\scripts\ScriptsUteis\Python\Transcript\TranscriptV2.py

if not exist "%PYTHON_SCRIPT%" (
    echo [ERRO] Script nao encontrado:
    echo %PYTHON_SCRIPT%
    echo.
    pause
    exit /b 1
)

REM ------------------------------------------------
REM SOLICITA O PATH AO USUARIO
REM ------------------------------------------------
set INPUT_PATH=

set /p INPUT_PATH=Informe o PATH para processamento: 

if "%INPUT_PATH%"=="" (
    echo.
    echo [ERRO] Nenhum path informado.
    pause
    exit /b 1
)

REM ------------------------------------------------
REM EXECUCAO
REM ------------------------------------------------
echo.
echo ----------------------------------------------
echo Executando:
echo python "%PYTHON_SCRIPT%" "%INPUT_PATH%"
echo ----------------------------------------------
echo.

python "%PYTHON_SCRIPT%" "%INPUT_PATH%"

REM ------------------------------------------------
REM STATUS FINAL
REM ------------------------------------------------
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERRO] O script terminou com erro.
    echo Codigo de retorno: %ERRORLEVEL%
) else (
    echo.
    echo [SUCESSO] Execucao finalizada com sucesso.
)

echo.
pause
