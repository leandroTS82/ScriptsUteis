@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

REM ==========================================================
REM CONFIG
REM ==========================================================

set HISTORY_FILE=%~dp0executed_scripts.history

REM ==========================================================
REM PREPARAÇÃO
REM ==========================================================

if not exist "%HISTORY_FILE%" (
    type nul > "%HISTORY_FILE%"
)

:MAIN_MENU
cls
echo ==============================================
echo 🚀 EXECUTOR DE SCRIPT COM HISTÓRICO
echo ==============================================
echo.

REM ==========================================================
REM LISTAR HISTÓRICO
REM ==========================================================

set INDEX=0
for /f "usebackq delims=" %%A in ("%HISTORY_FILE%") do (
    set /a INDEX+=1
    echo  !INDEX!) %%A
)

if %INDEX% EQU 0 (
    echo  (nenhum script salvo ainda)
)

echo.
echo Digite o NUMERO para executar um script salvo
echo Digite N para informar um novo caminho
echo Digite Q para sair
echo.

set CHOICE=
set /p CHOICE=👉 Sua escolha: 

if /I "%CHOICE%"=="Q" goto EXIT
if /I "%CHOICE%"=="N" goto NEW_SCRIPT

REM ==========================================================
REM ESCOLHA NUMÉRICA
REM ==========================================================

set /a TEST_NUM=%CHOICE% 2>nul
if "%TEST_NUM%"=="" goto INVALID_CHOICE

set SELECTED_PATH=
set CURRENT=0

for /f "usebackq delims=" %%A in ("%HISTORY_FILE%") do (
    set /a CURRENT+=1
    if "!CURRENT!"=="%CHOICE%" (
        set SELECTED_PATH=%%A
    )
)

if "%SELECTED_PATH%"=="" goto INVALID_CHOICE
goto RUN_SCRIPT

REM ==========================================================
REM NOVO SCRIPT
REM ==========================================================

:NEW_SCRIPT
echo.
set SELECTED_PATH=
set /p SELECTED_PATH=👉 Informe o caminho completo do script (.py ou .ps1): 

if "%SELECTED_PATH%"=="" goto MAIN_MENU

if not exist "%SELECTED_PATH%" (
    echo.
    echo ❌ Arquivo não encontrado:
    echo %SELECTED_PATH%
    pause
    goto MAIN_MENU
)

REM ----------------------------------------------------------
REM SALVAR NO HISTÓRICO (SEM DUPLICAR)
REM ----------------------------------------------------------

findstr /x /c:"%SELECTED_PATH%" "%HISTORY_FILE%" >nul
if errorlevel 1 (
    echo %SELECTED_PATH%>>"%HISTORY_FILE%"
)

goto RUN_SCRIPT

REM ==========================================================
REM EXECUÇÃO
REM ==========================================================

:RUN_SCRIPT
echo.
echo 📄 Script selecionado:
echo %SELECTED_PATH%
echo.

set EXT=%SELECTED_PATH:~-4%

if /I "%EXT%"==".py" (
    echo ▶ Tipo: Python
    echo ▶ Executando...
    echo.
    python "%SELECTED_PATH%"
    set EXIT_CODE=%ERRORLEVEL%
    goto RESULT
)

if /I "%EXT%"==".ps1" (
    echo ▶ Tipo: PowerShell
    echo ▶ Executando...
    echo.
    powershell -ExecutionPolicy Bypass -File "%SELECTED_PATH%"
    set EXIT_CODE=%ERRORLEVEL%
    goto RESULT
)

echo.
echo ❌ Tipo de arquivo não suportado.
echo Apenas .py ou .ps1
pause
goto MAIN_MENU

REM ==========================================================
REM RESULTADO
REM ==========================================================

:RESULT
echo.
if %EXIT_CODE% EQU 0 (
    echo ✅ SCRIPT EXECUTADO COM SUCESSO
) else (
    echo ❌ SCRIPT FINALIZOU COM ERRO
    echo Código de saída: %EXIT_CODE%
)

echo.
pause
goto MAIN_MENU

REM ==========================================================
REM ERROS
REM ==========================================================

:INVALID_CHOICE
echo.
echo ❌ Escolha inválida.
pause
goto MAIN_MENU

REM ==========================================================
REM SAÍDA
REM ==========================================================

:EXIT
echo.
echo 👋 Encerrando executor...
echo.
pause
endlocal