@echo off
chcp 65001 > nul
title Python Script Runner
echo ==================================================
echo        🤖 EKF - Englis hKnowledge Framework
echo ==================================================
REM =====================================================
REM CONFIGURAÇÃO
REM Informe o caminho COMPLETO do arquivo .py
REM =====================================================

set PY_SCRIPT_PATH=C:\dev\scripts\ScriptsUteis\Python\EKF_EnglishKnowledgeFramework\run_f.py

REM =====================================================
REM EXECUÇÃO
REM =====================================================

echo.
echo ============================================
echo Executando script Python:
echo %PY_SCRIPT_PATH%
echo ============================================
echo.

python "%PY_SCRIPT_PATH%"

echo.
echo ============================================
echo Execução finalizada.
echo Pressione qualquer tecla para sair.
echo ============================================
pause > nul
