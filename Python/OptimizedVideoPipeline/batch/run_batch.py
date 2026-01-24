import os
import sys
import json
from pathlib import Path

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

CREATE_LATER = Path("CreateLater.json")

with open(CREATE_LATER, "r", encoding="utf-8") as f:
    pending = json.load(f).get("pending", [])

if not pending:
    print("ℹ️ Nada para processar.")
    sys.exit(0)

for word in pending:
    print(f"▶ Processando: {word}")
    os.system(f'{sys.executable} batch/process_word.py "{word}"')

with open(CREATE_LATER, "w", encoding="utf-8") as f:
    json.dump({"pending": []}, f, indent=2, ensure_ascii=False)

print("✅ Batch concluído.")
