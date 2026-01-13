# ============================================================
# anki_english_trainer.py
# Anki-style English Trainer using Groq
# ============================================================

import os
import json
import random
import time
import requests
import re
import unicodedata
from typing import Dict, List

# ============================================================
# CONFIGURAÇÕES
# ============================================================

TERMS_SOURCE_JSON = "./english_terms.json"
VOCAB_DB_FILE = "./vocab_bank.json"

GROQ_KEYS_JSON = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\FilesHelper\secret_tokens_keys\GroqKeys.json"

GROQ_MODEL = "openai/gpt-oss-20b"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

SLEEP_BETWEEN_CALLS = 0.6

# 🔥 NOVA CONFIGURAÇÃO
MAX_CORRECT_PER_TERM = 5

# ============================================================
# 🎨 CORES (ANSI)
# ============================================================

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
RESET = "\033[0m"

# ============================================================
# 🔑 GROQ KEYS — INLINE
# ============================================================

#GROQ_KEYS_INLINE = [
 #   {"name": "lts@gmail.com", "key": "gsk_rCgiejl0b********"},
 #   {"name": "ltsCV@gmail", "key": "gsk_4d6mJ88RV********"},
 #   {"name": "butterfly", "key": "gsk_nx2OluxvI********"},
 #   {"name": "??", "key": "gsk_PPgOasIYR********"},
 #   {"name": "MelLuz201811@gmail.com", "key": "gsk_pXuAEvC4R********"},
#]
#Adicione as keys aqui como no exemplo acima
GROQ_KEYS_INLINE = []

# ============================================================
# GROQ – LOAD KEYS
# ============================================================

def extract_valid_keys(entries: List[dict]) -> List[str]:
    return [e["key"].strip() for e in entries if (e.get("key") or "").startswith("gsk_")]


def load_groq_keys() -> List[str]:
    inline = extract_valid_keys(GROQ_KEYS_INLINE)
    if inline:
        print(f"🔑 Groq keys carregadas do código: {len(inline)}")
        return inline

    with open(GROQ_KEYS_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    file_keys = extract_valid_keys(data)
    if not file_keys:
        raise RuntimeError("❌ Nenhuma Groq Key válida.")

    return file_keys


GROQ_KEYS = load_groq_keys()

# ============================================================
# GROQ CALL
# ============================================================

def call_groq(prompt: str) -> str:
    key = random.choice(GROQ_KEYS)

    response = requests.post(
        GROQ_URL,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        json={
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": "You are an English teacher. Return ONLY valid JSON."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
        },
        timeout=60,
    )

    response.raise_for_status()
    time.sleep(SLEEP_BETWEEN_CALLS)
    return response.json()["choices"][0]["message"]["content"]

# ============================================================
# NORMALIZAÇÃO
# ============================================================

def normalize_answer(text: str) -> str:
    text = text.strip().lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^\w\s]", "", text)
    return re.sub(r"\s{2,}", " ", text).strip()


def local_match(a: str, b: str) -> bool:
    return normalize_answer(a) == normalize_answer(b)

# ============================================================
# JSON SAFE PARSER
# ============================================================

def safe_json_parse(text: str) -> dict:
    try:
        return json.loads(text.strip())
    except Exception:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            return json.loads(match.group())
    raise ValueError("Resposta não contém JSON válido.")

# ============================================================
# VOCAB DB
# ============================================================

def load_vocab_db() -> Dict[str, dict]:
    if not os.path.exists(VOCAB_DB_FILE):
        return {}
    with open(VOCAB_DB_FILE, "r", encoding="utf-8") as f:
        db = json.load(f)

    for v in db.values():
        v.setdefault("stats", {})
        v["stats"].setdefault("seen", 0)
        v["stats"].setdefault("correct", 0)
        v["stats"].setdefault("wrong", 0)
        v["stats"].setdefault("dont_know", 0)

    return db


def save_vocab_db(db: Dict[str, dict]):
    with open(VOCAB_DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

# ============================================================
# ENRICH TERM (GROQ)
# ============================================================

def enrich_term(term: str) -> dict | None:
    prompt = f"""
For the English term "{term}", return JSON with:
translation_pt,
definition_en (en e pt),
example_1,
example_2,
common_expressions
"""
    try:
        data = safe_json_parse(call_groq(prompt))
    except Exception:
        return None

    return {
        "translation": data.get("translation_pt", ""),
        "definition": data.get("definition_en", ""),
        "examples": [data.get("example_1", ""), data.get("example_2", "")],
        "expressions": list(dict.fromkeys(data.get("common_expressions", []))),
    }

# ============================================================
# HEADER
# ============================================================

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def progress_bar(pct: float, width: int = 25) -> str:
    filled = int(width * pct / 100)
    return "█" * filled + "░" * (width - filled)


def render_header(db: Dict[str, dict]):
    seen = correct = wrong = dont = 0

    for v in db.values():
        s = v["stats"]
        seen += s["seen"]
        correct += s["correct"]
        wrong += s["wrong"]
        dont += s["dont_know"]

    def pct(x):
        return (x / seen * 100) if seen else 0.0

    print(f"{CYAN} PROGRESSO GERAL{RESET}")
    print(f"{GREEN}✅ Acertos : {progress_bar(pct(correct))} {pct(correct):6.2f}%{RESET}")
    print(f"{RED}❌ Erros   : {progress_bar(pct(wrong))} {pct(wrong):6.2f}%{RESET}")
    print(f"{YELLOW}🤷 Não sei : {progress_bar(pct(dont))} {pct(dont):6.2f}%{RESET}")
    print("-" * 60)

# ============================================================
# DETALHES
# ============================================================

def show_details(entry: dict):
    print(f"\n{MAGENTA}📘 Definição:{RESET}")
    print(entry.get("definition", ""))

    print(f"\n{MAGENTA}📝 Exemplos:{RESET}")
    for ex in entry.get("examples", []):
        print(f" - {ex}")

    print(f"\n{MAGENTA}🔗 Expressões:{RESET}")
    for exp in entry.get("expressions", []):
        print(f" - {exp}")

# ============================================================
# JOGO
# ============================================================

def play(db: Dict[str, dict]):
    while True:
        clear_screen()
        render_header(db)

        # 🔥 FILTRO POR LIMITE DE ACERTOS
        eligible_terms = [
            term for term, data in db.items()
            if data["stats"]["correct"] < MAX_CORRECT_PER_TERM
        ]

        if not eligible_terms:
            print(f"{GREEN}  Todos os termos atingiram {MAX_CORRECT_PER_TERM} acertos!{RESET}")
            return

        random.shuffle(eligible_terms)
        term = eligible_terms[0]
        entry = db[term]
        stats = entry["stats"]

        print(f"\n🔤 {CYAN}Termo:{RESET} {term}")
        user = input("✍️ Tradução (n = não sei | s = sair): ").strip().lower()

        if user == "s":
            save_vocab_db(db)
            return

        stats["seen"] += 1

        if user == "n":
            stats["dont_know"] += 1
            print(f"{YELLOW}👉 Tradução:{RESET} {entry['translation']}")
        else:
            if local_match(user, entry["translation"]):
                stats["correct"] += 1
                print(f"{GREEN}✅ Correto!{RESET}")
            else:
                stats["wrong"] += 1
                print(f"{RED}❌ Incorreto.{RESET}")
                print(f"{YELLOW}👉 Correto:{RESET} {entry['translation']}")

        show_details(entry)
        save_vocab_db(db)

        cmd = input("\n↩️ ENTER = próximo | s = sair: ").strip().lower()
        if cmd == "s":
            return

# ============================================================
# MAIN MENU
# ============================================================

def main():
    vocab_db = load_vocab_db()

    clear_screen()
    print("Digite:")
    print(" I → iniciar jogo")
    print(" R → reenriquecer termos")
    print(" S → sair")

    cmd = input("Opção: ").strip().lower()

    if cmd == "r":
        for term, entry in vocab_db.items():
            print(f"🌐 Reenriquecendo: {term}")
            enriched = enrich_term(term)
            if enriched:
                entry.update(enriched)
                save_vocab_db(vocab_db)
        print("✅ Reenriquecimento concluído.")
        return

    if cmd == "i":
        play(vocab_db)


if __name__ == "__main__":
    main()