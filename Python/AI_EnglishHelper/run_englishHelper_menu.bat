@echo off
chcp 65001 >nul
setlocal
color 0A

:MENU
cls
echo ==================================================
echo        🤖 AI ENGLISH HELPER - MENU PRINCIPAL
echo ==================================================
echo.
echo  1  - 🧠 Context Builder (Acumulativo / Narrativa / Canção)
echo  2  - 📘 Transcript + Wordbank (CreateLater / PDF)
echo  3  - 🔍 Enriched English Explainer (Active English)
echo.
echo  Digite o numero da opcao
echo  ou digite "s" para sair
echo.
set /p OPCAO=👉 Escolha: 

if /i "%OPCAO%"=="s" goto SAIR

REM === ORDEM SEGURA (MAIOR PARA MENOR) ===
if "%OPCAO%"=="3" goto OP3
if "%OPCAO%"=="2" goto OP2
if "%OPCAO%"=="1" goto OP1

echo.
echo ❌ Opcao invalida.
pause
goto MENU

:OP1
cls
color 0B
echo ▶ 🧠 Context Builder — Acumulativo / Narrativa / Canção
cd /d "C:\Dev\GitLTS\ScriptsUteis\Python\AI_EnglishHelper"
python w_context.py
pause
goto MENU

:OP2
cls
color 0E
echo ▶ 📘 Transcript + Wordbank (Groq Only)
cd /d "C:\Dev\GitLTS\ScriptsUteis\Python\AI_EnglishHelper"
python w.py
pause
goto MENU

:OP3
cls
color 0D
echo ▶ 🔍 Enriched English Explainer (Active English)
cd /d "C:\Dev\GitLTS\ScriptsUteis\Python\AI_EnglishHelper"
python e.py
pause
goto MENU

:SAIR
color 07
echo.
echo 👋 Encerrando menu...
timeout /t 1 >nul
exit