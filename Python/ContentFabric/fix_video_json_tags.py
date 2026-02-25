"""
============================================================
 Script: fix_video_json_tags.py
 Autor: Leandro
 Descrição:
   - Corrige JSONs onde 'tags' está como string
   - Converte para array de strings
============================================================
"""

import json
from pathlib import Path

VIDEOS_DIR = Path(
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos"
)

def normalize_tags(tag_string: str) -> list[str]:
    return [
        t.strip()
        for t in tag_string.split(",")
        if t.strip()
    ]

def process_json(json_path: Path) -> bool:
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))

        tags = data.get("tags")
        if isinstance(tags, str):
            data["tags"] = normalize_tags(tags)
            json_path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            return True

    except Exception as e:
        print(f"❌ Erro em {json_path.name}: {e}")

    return False

def main():
    if not VIDEOS_DIR.exists():
        print("❌ Diretório não encontrado:")
        print(VIDEOS_DIR)
        return

    json_files = list(VIDEOS_DIR.rglob("*.json"))
    fixed = 0

    print("\n==================================================")
    print("🛠️  CORREÇÃO DE TAGS (JSON)")
    print("==================================================\n")

    for jf in json_files:
        if process_json(jf):
            print(f"✅ Corrigido: {jf.name}")
            fixed += 1

    print("\n--------------------------------------------------")
    print(f"JSONs analisados: {len(json_files)}")
    print(f"JSONs corrigidos: {fixed}")
    print("--------------------------------------------------\n")

if __name__ == "__main__":
    main()