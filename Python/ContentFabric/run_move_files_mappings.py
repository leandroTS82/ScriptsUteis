"""
============================================================
 Script: run_move_files_mappings.py
 Autor: Leandro
 Descrição:
   - Executa o PowerShell de movimentação de arquivos por mapeamento
   - Força encoding UTF-8
   - Compatível com BAT, menu interativo ou execução direta
   - Mostra saída do PowerShell em tempo real
============================================================
"""

import subprocess
import sys
from pathlib import Path

# ==========================================================
# CONFIGURAÇÕES INLINE
# ==========================================================

POWERSHELL_EXE = "powershell"   # use "pwsh" se estiver no PowerShell 7+
PS_SCRIPT_PATH = Path(
    r"C:\dev\scripts\ScriptsUteis\PowerShell\move_files_by_mapping.ps1"
)

# ==========================================================
# VALIDAÇÕES
# ==========================================================

if not PS_SCRIPT_PATH.exists():
    print("❌ Script PowerShell não encontrado:")
    print(PS_SCRIPT_PATH)
    sys.exit(1)

# ==========================================================
# COMANDO POWERSHELL (ROBUSTO / UTF-8)
# ==========================================================

command = [
    POWERSHELL_EXE,
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-Command",
    (
        "[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new(); "
        "$ErrorActionPreference = 'Stop'; "
        f"& '{PS_SCRIPT_PATH}'"
    )
]

# ==========================================================
# EXECUÇÃO
# ==========================================================

print("▶ Executando PowerShell: MOVE FILES BY MAPPING\n")

process = subprocess.Popen(
    command,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    encoding="utf-8",
    errors="replace"
)

# Stream em tempo real (stdout)
while True:
    line = process.stdout.readline()
    if line:
        print(line, end="")
    elif process.poll() is not None:
        break

# Captura stderr (se houver)
stderr = process.stderr.read()
if stderr.strip():
    print("\n⚠️ ERROS / AVISOS DO POWERSHELL:")
    print(stderr)

exit_code = process.returncode

print("\n==================================================")
if exit_code == 0:
    print("✅ Processo PowerShell finalizado com sucesso.")
else:
    print(f"❌ Processo PowerShell finalizado com erro. ExitCode={exit_code}")
print("==================================================\n")

sys.exit(exit_code)