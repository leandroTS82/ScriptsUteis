import json
import os
import sys

# ============================================================
# BASE DIR (PADRÃO PARA DEPENDÊNCIAS LOCAIS)
# ============================================================

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# ============================================================
# PATHS
# ============================================================

ENGLISH_TERMS_FLAT = r"C:\dev\scripts\ScriptsUteis\Python\Transcript\output\english_terms_flat.json"
TERMS_FROM_MOVIES  = r"C:\dev\scripts\ScriptsUteis\Python\english_terms\terms_From_Movies.json"

OUTPUT_FILE = "./pending_terms.json"
IGNORE_TERMS_FILE = "./check_pending_ignore_terms.json"

# ============================================================
# HELPERS
# ============================================================

def normalize(term: str) -> str:
    return term.strip().lower()

# ============================================================
# LOAD FILES
# ============================================================

if not os.path.exists(ENGLISH_TERMS_FLAT):
    raise FileNotFoundError(f"Arquivo não encontrado: {ENGLISH_TERMS_FLAT}")

if not os.path.exists(TERMS_FROM_MOVIES):
    raise FileNotFoundError(f"Arquivo não encontrado: {TERMS_FROM_MOVIES}")

if not os.path.exists(IGNORE_TERMS_FILE):
    raise FileNotFoundError(f"Arquivo não encontrado: {IGNORE_TERMS_FILE}")

with open(ENGLISH_TERMS_FLAT, "r", encoding="utf-8") as f:
    flat_terms_raw = json.load(f)

with open(TERMS_FROM_MOVIES, "r", encoding="utf-8") as f:
    movie_terms_raw = json.load(f)

with open(IGNORE_TERMS_FILE, "r", encoding="utf-8") as f:
    ignore_terms_raw = json.load(f)

# ============================================================
# NORMALIZATION
# ============================================================

flat_terms = [
    normalize(item["term"])
    for item in flat_terms_raw
    if isinstance(item, dict) and "term" in item
]

movie_terms = {
    normalize(term)
    for term in movie_terms_raw
    if isinstance(term, str)
}

IGNORE_TERMS = {
    normalize(term)
    for term in ignore_terms_raw.get("ignore", [])
    if isinstance(term, str)
}

# ============================================================
# DIFF
# ============================================================

pending_terms = sorted([
    term for term in flat_terms
    if term not in movie_terms and term not in IGNORE_TERMS
])

# ============================================================
# OUTPUT
# ============================================================

output = {
    "pending": pending_terms
}

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"✔ JSON gerado com sucesso: {OUTPUT_FILE}")
print(f"✔ Total de termos pendentes: {len(pending_terms)}")
