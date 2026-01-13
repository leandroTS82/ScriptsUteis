import os
import json
import sys

# ============================================================
# CONFIG
# ============================================================

# Path via CLI ou fixo
# Exemplo:
#   python list_files_to_json.py "C:\meu\diretorio"

TARGET_PATH = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\leand\Desktop\wordbank"
OUTPUT_JSON = "./terms_From_Movies.json"

# ============================================================
# PROCESS
# ============================================================

if not os.path.exists(TARGET_PATH):
    raise FileNotFoundError(f"Path não encontrado: {TARGET_PATH}")

result = []

for root, _, files in os.walk(TARGET_PATH):
    for file in files:
        name_without_ext = os.path.splitext(file)[0]
        cleaned_name = name_without_ext.replace("_", " ")
        result.append(cleaned_name)

# ============================================================
# OUTPUT
# ============================================================

with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"JSON gerado com {len(result)} itens → {OUTPUT_JSON}")
