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
import sys
from typing import Dict, List
from itertools import cycle

# ============================================================
# CONFIGURAÇÕES
# ============================================================

BASE_TERMS_DIR = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\EKF_EnglishKnowledgeFramework_REPO\BaseTerms"
VOCAB_DB_FILE = "C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\EKF_EnglishKnowledgeFramework_REPO\vocab_bank.json"

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b"

SLEEP_BETWEEN_CALLS = 0.6
MAX_CORRECT_PER_TERM = 5

ENABLE_GROQ_VALIDATION = True
ENABLE_GROQ_WRONG_FEEDBACK = True

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
# 🔑 GROQ KEYS – RANDOM ROTATION
# ============================================================

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from groq_keys_loader import GROQ_KEYS

_groq_key_cycle = cycle(random.sample(GROQ_KEYS, len(GROQ_KEYS)))

def get_next_groq_key() -> str:
    for _ in range(len(GROQ_KEYS)):
        key = next(_groq_key_cycle).get("key", "").strip()
        if key.startswith("gsk_"):
            return key
    raise RuntimeError("❌ Nenhuma GROQ API Key válida encontrada.")

# ============================================================
# GROQ CALL
# ============================================================

def call_groq(prompt: str) -> str:
    last_error = None

    for _ in range(len(GROQ_KEYS)):
        api_key = get_next_groq_key()

        try:
            response = requests.post(
                GROQ_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": GROQ_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are an English teacher. Return ONLY valid JSON."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.2,
                },
                timeout=60,
            )

            if response.status_code == 429:
                last_error = "Rate limit"
                continue

            response.raise_for_status()
            time.sleep(SLEEP_BETWEEN_CALLS)

            return response.json()["choices"][0]["message"]["content"]

        except Exception as e:
            last_error = str(e)
            continue

    raise RuntimeError(f"❌ Todas as GROQ keys falharam. Último erro: {last_error}")

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
# GROQ – SEMANTIC VALIDATION
# ============================================================

def groq_validate_translation(term: str, user_answer: str, correct_translation: str) -> bool:
    prompt = f"""
English term: "{term}"
Expected meaning (Portuguese): "{correct_translation}"
User answer: "{user_answer}"

Is the meaning correct?
Accept synonyms and minor spelling mistakes.

Return:
{{ "is_correct": true | false }}
"""
    try:
        data = safe_json_parse(call_groq(prompt))
        return bool(data.get("is_correct"))
    except Exception:
        return False

# ============================================================
# GROQ – WRONG ANSWER FEEDBACK
# ============================================================

def groq_wrong_feedback(term: str, user_answer_pt: str, correct_translation_pt: str) -> dict | None:
    prompt = f"""
English term: "{term}"
User answer (PT): "{user_answer_pt}"
Correct meaning (PT): "{correct_translation_pt}"

Explain briefly and return:
{{
  "mistake_pt": "...",
  "example_en": "...",
  "example_pt": "..."
}}
"""
    try:
        data = safe_json_parse(call_groq(prompt))
        return {
            "mistake_pt": data.get("mistake_pt", ""),
            "example_en": data.get("example_en", ""),
            "example_pt": data.get("example_pt", "")
        }
    except Exception:
        return None

# ============================================================
# ENRICH TERM
# ============================================================

def enrich_term(term: str) -> dict | None:
    prompt = f"""
For the English term "{term}", return JSON:

{{
  "translation_pt": "...",
  "definition_en": "...",
  "example_1": "...",
  "example_2": "...",
  "common_expressions": ["...", "..."]
}}
"""
    try:
        data = safe_json_parse(call_groq(prompt))
    except Exception:
        return None

    return {
        "term": term,
        "translation": data.get("translation_pt", "").strip(),
        "definition": data.get("definition_en", "").strip(),
        "examples": [
            data.get("example_1", "").strip(),
            data.get("example_2", "").strip()
        ],
        "expressions": list(dict.fromkeys(data.get("common_expressions", [])))
    }

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
# CONSOLIDAÇÃO BASE TERMS
# ============================================================

def consolidate_terms():
    terms = {}

    for file in os.listdir(BASE_TERMS_DIR):
        if file.endswith(".json"):
            path = os.path.join(BASE_TERMS_DIR, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for term in data.get("pending", []):
                        norm = normalize_answer(term)
                        if norm and norm not in terms:
                            terms[norm] = term.strip()
            except Exception:
                continue

    return list(terms.values())

# ============================================================
# REENRIQUECER
# ============================================================

def reenrich_all_terms():
    vocab_db = load_vocab_db()
    consolidated = consolidate_terms()

    print(f"\n📚 Total termos encontrados: {len(consolidated)}\n")

    for term in consolidated:
        if term in vocab_db:
            print(f"⏭️ Já existe no vocab: {term}")
            continue

        print(f"🌐 Criando novo termo: {term}")

        enriched = enrich_term(term)
        if not enriched:
            print("   ⚠️ Falha ao enriquecer.")
            continue

        enriched["stats"] = {
            "seen": 0,
            "correct": 0,
            "wrong": 0,
            "dont_know": 0
        }

        vocab_db[term] = enriched
        save_vocab_db(vocab_db)

    print("\n✅ Reenriquecimento concluído.")


# ============================================================
# UI HELPERS
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
# DETAILS
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
# GAME
# ============================================================

def play(db: Dict[str, dict]):
    while True:
        clear_screen()
        render_header(db)

        eligible_terms = [
            term for term, data in db.items()
            if data["stats"]["correct"] < MAX_CORRECT_PER_TERM
        ]

        if not eligible_terms:
            print(f"{GREEN}🎉 Todos os termos dominados!{RESET}")
            return

        term = random.choice(eligible_terms)
        entry = db[term]
        stats = entry["stats"]

        print(f"\n🔤 {CYAN}Termo:{RESET} {term}")
        user = input("✍️ Tradução (n = não sei | s = sair): ").strip()

        if user.lower() == "s":
            save_vocab_db(db)
            return

        stats["seen"] += 1

        if user.lower() == "n":
            stats["dont_know"] += 1
            print(f"{YELLOW}👉 Tradução:{RESET} {entry['translation']}")

        elif local_match(user, entry["translation"]):
            stats["correct"] += 1
            print(f"{GREEN}✅ Correto!{RESET}")

        elif ENABLE_GROQ_VALIDATION and groq_validate_translation(
            term, user, entry["translation"]
        ):
            stats["correct"] += 1
            print(f"{CYAN}🤖 Correto (validação semântica)!{RESET}")
            print(f"{YELLOW}👉 Tradução aceita:{RESET} {entry['translation']}")

        else:
            stats["wrong"] += 1
            print(f"{RED}❌ Incorreto.{RESET}")
            print(f"{YELLOW}👉 Correto:{RESET} {entry['translation']}")

            if ENABLE_GROQ_WRONG_FEEDBACK:
                fb = groq_wrong_feedback(term, user, entry["translation"])
                if fb:
                    print(f"\n{CYAN}🤖 Feedback:{RESET}")
                    print(f"{MAGENTA}• Erro:{RESET} {fb['mistake_pt']}")
                    print(f"{MAGENTA}• Exemplo EN:{RESET} {fb['example_en']}")
                    print(f"{MAGENTA}• Tradução PT:{RESET} {fb['example_pt']}")

        show_details(entry)
        save_vocab_db(db)

        cmd = input("\n↩️ ENTER = próximo | s = sair: ").strip().lower()
        if cmd == "s":
            return

# ============================================================
# MAIN
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
        reenrich_all_terms()
        input("\nPressione ENTER para continuar...")
        return

    if cmd == "i":
        play(vocab_db)

if __name__ == "__main__":
    main()
