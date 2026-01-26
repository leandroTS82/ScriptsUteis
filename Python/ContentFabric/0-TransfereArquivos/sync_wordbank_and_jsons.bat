@echo off
chcp 65001 >nul
setlocal

echo ============================================================
echo INICIO DO PROCESSO
echo Data/Hora: %DATE% %TIME%
echo ============================================================
echo.

REM ---- PYTHON ----
where python >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado no PATH.
    goto :end
)

REM ---- SCRIPT ----
set SCRIPT_PATH=C:\dev\scripts\ScriptsUteis\Python\ContentFabric\0-TransfereArquivos\sync_wordbank_and_jsons.py

if not exist "%SCRIPT_PATH%" (
    echo ERRO: Script Python nao encontrado:
    echo %SCRIPT_PATH%
    goto :end
)

echo Executando script Python...
echo.

python "%SCRIPT_PATH%"
set EXIT_CODE=%ERRORLEVEL%

echo.
echo Script finalizado. ExitCode=%EXIT_CODE%
echo.

if not "%EXIT_CODE%"=="0" (
    echo PROCESSO FINALIZADO COM ERRO
) else (
    echo PROCESSO FINALIZADO COM SUCESSO
)

:end
echo.
echo Pressione qualquer tecla para fechar...
pause >nul
exit /b %EXIT_CODE%
