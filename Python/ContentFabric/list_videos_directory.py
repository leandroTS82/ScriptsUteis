"""
============================================================
 Script: list_videos_directory.py
 Autor: Leandro
 Descrição:
   - Lista arquivos e pastas do diretório de vídeos
============================================================
"""

from pathlib import Path

VIDEOS_DIR = Path(
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS"
    r"\LTS SP Site - VideosGeradosPorScript\Videos"
)

def main():
    if not VIDEOS_DIR.exists():
        print("❌ Diretório não encontrado:")
        print(VIDEOS_DIR)
        return

    items = sorted(VIDEOS_DIR.iterdir(), key=lambda x: x.name.lower())

    print("\n==================================================")
    print("📂 LISTAGEM DE VÍDEOS GERADOS")
    print("==================================================\n")

    if not items:
        print("⚠️ Diretório vazio.")
        return

    for item in items:
        prefix = "📁" if item.is_dir() else "🎬"
        print(f"{prefix} {item.name}")

    print("\n--------------------------------------------------")
    print(f"Total de itens: {len(items)}")
    print("--------------------------------------------------\n")

if __name__ == "__main__":
    main()