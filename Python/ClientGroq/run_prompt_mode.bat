@echo off
cls

echo =====================================
echo     SELECIONE O MODO DE PROMPT
echo =====================================
echo.
echo 1 - Modo Programador
echo 2 - Modo Curiosidade
echo.

set /p MODE=Digite o numero do modo: 

if "%MODE%"=="1" (
    set PROMPT_MODE=programador
) else if "%MODE%"=="2" (
    set PROMPT_MODE=curiosidade
) else (
    echo Opcao invalida.
    pause
    exit /b
)

echo.
set /p USER_TEXT=Digite o texto adicional (ou ENTER para nenhum): 

python roq_chat_runner.py %PROMPT_MODE% "%USER_TEXT%"

pause
