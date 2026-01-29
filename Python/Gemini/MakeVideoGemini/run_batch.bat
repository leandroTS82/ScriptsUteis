@echo off
chcp 65001 >nul
setlocal

REM ==========================================================
REM BAT: run_batch.bat
REM Descrição:
REM   - Executa o script run_batch.py
REM   - Exibe feedback de sucesso ou erro
REM ==========================================================

echo.
echo ==============================================
echo 🚀 INICIANDO EXECUÇÃO DO MAKE VIDEO GEMINI
echo ==============================================
echo.

REM Caminho do Python (usa o do PATH)
set PYTHON_CMD=python

REM Caminho do script
set SCRIPT_PATH=C:\dev\scripts\ScriptsUteis\Python\Gemini\MakeVideoGemini\run_batch2.py

REM Verificação do arquivo
if not exist "%SCRIPT_PATH%" (
    echo ❌ ERRO: Script não encontrado!
    echo Caminho esperado:
    echo %SCRIPT_PATH%
    echo.
    pause
    exit /b 1
)

echo ▶ Executando:
echo %SCRIPT_PATH%
echo.

%PYTHON_CMD% "%SCRIPT_PATH%"
set EXIT_CODE=%ERRORLEVEL%

echo.
if %EXIT_CODE% EQU 0 (
    echo ✅ EXECUÇÃO FINALIZADA COM SUCESSO
) else (
    echo ❌ EXECUÇÃO FINALIZADA COM ERRO
    echo Código de erro: %EXIT_CODE%
)

echo.
echo ==============================================
echo 🛑 FIM DO PROCESSO
echo ==============================================
echo.
pause
endlocal
