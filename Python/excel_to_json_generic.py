import os
import json
import re
import pandas as pd
from collections import defaultdict

# ======================================
# CONFIGURAÇÃO GENÉRICA
# ======================================
EXCEL_FILE = "./files/Faqs.xlsx"
OUTPUT_DIR = "./files/excelTojson"
OUTPUT_FILE = "output_excel_to_json_generic.json"

LANG_PATTERN = re.compile(r"(.+?)\s*\((.+?)\)$", re.IGNORECASE)

# ======================================
# LOAD
# ======================================
df = pd.read_excel(EXCEL_FILE)
df.columns = [c.strip() for c in df.columns]

# ======================================
# TRANSFORMAÇÃO GENÉRICA
# ======================================
rows = []

for _, row in df.iterrows():
    item = {}
    multi_lang = defaultdict(dict)

    for col in df.columns:
        value = row[col]

        if pd.isna(value):
            continue

        match = LANG_PATTERN.match(col)
        if match:
            base_key = match.group(1).strip().replace(" ", "_").lower()
            lang = match.group(2).strip().lower()
            multi_lang[base_key][lang] = str(value).strip()
        else:
            key = col.replace(" ", "_").lower()
            item[key] = str(value).strip()

    # mescla multilíngue
    for k, v in multi_lang.items():
        item[k] = v

    rows.append(item)

# ======================================
# OUTPUT
# ======================================
os.makedirs(OUTPUT_DIR, exist_ok=True)
output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(rows, f, ensure_ascii=False, indent=2)

print(f"✔ Arquivo gerado: {output_path}")
print(f"✔ Registros exportados: {len(rows)}")
