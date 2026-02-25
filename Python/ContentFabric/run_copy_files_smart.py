"""
============================================================
 Script: copy_files_smart.py
 Autor: Leandro
 Descrição:
   - Replica a lógica do COPY FILES SMART (PowerShell)
   - Copia arquivos de múltiplas origens para destinos
   - Controle de subpastas com exceções
   - Filtros por extensão e sufixo
   - Ignora arquivos já existentes
============================================================
"""

from pathlib import Path
import shutil

# ==========================================================
# CONFIGURAÇÃO GLOBAL
# ==========================================================

# 🔁 Comportamento padrão: NÃO varrer subpastas
INCLUDE_SUBFOLDERS = False

# 🔁 EXCEÇÕES: apenas estes sources varrem subpastas
SOURCES_WITH_SUBFOLDERS = {
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\Communication site - ReunioesGravadas"
}

# ==========================================================
# PATH MAPPINGS
# ==========================================================

PATH_MAPPINGS = [

    # =========================
    # WORD BANK
    # =========================
    {
        "source": r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\VideosSemJson",
        "destination": r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - LeandrinhoMovies",
        "extensions": ["mp4"],
    },
    {
        "source": r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\Youtube_Upload_Faulty_File",
        "destination": r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - LeandrinhoMovies",
        "extensions": ["mp4"],
    },
    {
        "source": r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\Videos",
        "destination": r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - LeandrinhoMovies",
        "extensions": ["mp4"],
    },
    {
        "source": r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\Uploaded",
        "destination": r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - LeandrinhoMovies",
        "extensions": ["mp4"],
    },
    {
        "source": r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\EnableToYoutubeUpload",
        "destination": r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - LeandrinhoMovies",
        "extensions": ["mp4"],
    },
    {
        "source": r"C:\dev\scripts\ScriptsUteis\Python\Gemini\MakeVideoGemini\outputs\videos",
        "destination": r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - LeandrinhoMovies",
        "extensions": ["mp4"],
    },

    # =========================
    # HISTORIES
    # =========================
    {
        "source": r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\Histories",
        "destination": r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - LeandrinhoMovies\Histories",
        "extensions": ["mp4"],
    },
    {
        "source": r"C:\dev\scripts\ScriptsUteis\Python\Gemini\MakeHistorieMovie\outputs\videos",
        "destination": r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - LeandrinhoMovies\Histories",
        "extensions": ["mp4"],
    },
    {
        "source": r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\Histories\NewHistory",
        "destination": r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - LeandrinhoMovies\Histories",
        "extensions": ["mp4"],
    },

    # =========================
    # REUNIÕES (ÚNICO COM SUBPASTAS)
    # =========================
    {
        "source": r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\Communication site - ReunioesGravadas",
        "destination": r"C:\Users\leand\Desktop\01-ReunioesGravadas",
        "extensions": ["mp4"],
        "endswith": ["_subbed"],
    },
]

# ==========================================================
# PROCESSAMENTO
# ==========================================================

def main():
    total_found = 0
    total_copied = 0
    total_skipped = 0

    print("\n==================================================")
    print("📂 COPY FILES SMART — Processo iniciado")
    print("==================================================\n")

    for mapping in PATH_MAPPINGS:
        source = Path(mapping["source"])
        dest = Path(mapping["destination"])
        extensions = {f".{e.lower()}" for e in mapping.get("extensions", [])}
        endswith = mapping.get("endswith", [])

        use_subfolders = INCLUDE_SUBFOLDERS or str(source) in SOURCES_WITH_SUBFOLDERS

        print("--------------------------------------------------")
        print(f"📁 Origem : {source}")
        print(f"📂 Destino: {dest}")
        print(f"📐 Subpastas: {use_subfolders}")

        if not source.exists():
            print("❌ Origem não encontrada. Pulando.")
            continue

        dest.mkdir(parents=True, exist_ok=True)

        files = (
            source.rglob("*")
            if use_subfolders
            else source.glob("*")
        )

        files = [f for f in files if f.is_file()]

        # -------- EXTENSIONS (AND)
        if extensions:
            files = [f for f in files if f.suffix.lower() in extensions]

        # -------- ENDS WITH (AND)
        if endswith:
            files = [
                f for f in files
                if all(f.stem.endswith(e) for e in endswith)
            ]

        if not files:
            print("ℹ️  Nenhum arquivo compatível encontrado.")
            continue

        for file in files:
            total_found += 1
            dest_file = dest / file.name

            if dest_file.exists():
                print(f"⏭️  Ignorado (já existe): {file.name}")
                total_skipped += 1
                continue

            shutil.copy2(file, dest_file)
            print(f"✅ Copiado: {file.name}")
            total_copied += 1

    # ======================================================
    # RESUMO
    # ======================================================

    print("\n==================================================")
    print("  RESUMO FINAL")
    print("==================================================")
    print(f" Encontrados : {total_found}")
    print(f"✅ Copiados  : {total_copied}")
    print(f"⏭️  Ignorados: {total_skipped}")
    print("\n Processo concluído com sucesso.\n")

if __name__ == "__main__":
    main()