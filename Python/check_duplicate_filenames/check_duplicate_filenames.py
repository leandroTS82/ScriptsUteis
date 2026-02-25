import os
import sys
from collections import defaultdict
from datetime import datetime

# ==========================================================
# CONFIGURAÇÕES
# ==========================================================

# PATH INLINE (PADRÃO)
DEFAULT_SCAN_PATH = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\EnableToYoutubeUpload"

OUTPUT_DIR = "./reportTxt"
REPORT_PREFIX = "duplicate_filenames_report"

# ==========================================================
# HELPERS
# ==========================================================

def log(msg: str):
    print(msg)

def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def normalize_filename(filename: str) -> str:
    """
    Normaliza para comparação:
    - case-insensitive
    """
    return filename.lower()

def scan_duplicates(base_path: str) -> dict:
    """
    Retorna:
    {
        "arquivo.ext": [
            "caminho/completo/1",
            "caminho/completo/2"
        ]
    }
    Apenas entradas com mais de 1 ocorrência.
    """
    files_map = defaultdict(list)

    for root, _, files in os.walk(base_path):
        for f in files:
            key = normalize_filename(f)
            full_path = os.path.join(root, f)
            files_map[key].append(full_path)

    # filtra apenas duplicados
    return {
        name: paths
        for name, paths in files_map.items()
        if len(paths) > 1
    }

def generate_report(duplicates: dict, scanned_path: str) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = []
    lines.append("============================================================")
    lines.append(" RELATÓRIO DE ARQUIVOS DUPLICADOS (NOME + EXTENSÃO)")
    lines.append("============================================================")
    lines.append(f"Path analisado : {scanned_path}")
    lines.append(f"Gerado em     : {now}")
    lines.append("")

    if not duplicates:
        lines.append("✅ Nenhum arquivo duplicado encontrado.")
        return "\n".join(lines)

    total_groups = len(duplicates)
    total_files = sum(len(v) for v in duplicates.values())

    lines.append(f"⚠️  Grupos duplicados encontrados : {total_groups}")
    lines.append(f"📄 Total de arquivos envolvidos   : {total_files}")
    lines.append("")

    for idx, (filename, paths) in enumerate(duplicates.items(), start=1):
        lines.append(f"{idx}. {filename}")
        for p in paths:
            lines.append(f"   - {p}")
        lines.append("")

    return "\n".join(lines)

def save_report(content: str) -> str:
    ensure_output_dir()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{REPORT_PREFIX}_{timestamp}.txt"
    output_path = os.path.join(OUTPUT_DIR, filename)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    return output_path

# ==========================================================
# MAIN
# ==========================================================

def main():
    # Prioridade:
    # 1. Argumento CLI
    # 2. Path inline
    if len(sys.argv) > 1:
        base_path = sys.argv[1]
    else:
        base_path = DEFAULT_SCAN_PATH

    if not os.path.exists(base_path):
        log("❌ Path informado não existe.")
        log(f"   {base_path}")
        return

    log("")
    log("🔍 Iniciando varredura...")
    log(f"📁 Path: {base_path}")
    log("")

    duplicates = scan_duplicates(base_path)
    report = generate_report(duplicates, base_path)

    # Preview no terminal
    print(report)

    # Salva arquivo
    output_file = save_report(report)

    log("")
    log("💾 Relatório salvo em:")
    log(f"   {os.path.abspath(output_file)}")
    log("")
    log("✅ Processo finalizado.")

if __name__ == "__main__":
    main()
