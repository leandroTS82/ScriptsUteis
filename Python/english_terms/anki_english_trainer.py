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
from typing import Dict, List

# ============================================================
# CONFIGURAÇÕES
# ============================================================

TERMS_SOURCE_JSON = "./english_terms.json"
VOCAB_DB_FILE = "./vocab_bank.json"

GROQ_KEYS_JSON = r"C:\dev\scripts\ScriptsUteis\Python\secret_tokens_keys\GroqKeys.json"

GROQ_MODEL = "openai/gpt-oss-20b"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

SLEEP_BETWEEN_CALLS = 0.6

# ============================================================
# 🔑 GROQ KEYS — INLINE (PRIORIDADE MÁXIMA)
# ============================================================

GROQ_KEYS_INLINE = [
    {"name": "lts@gmail.com", "key": "gs****8xltig9"},
    {"name": "ltsCV@gmail", "key": "gsk_4d******f"},
    {"name": "butterfly", "key": "gsk_n*********l9wwYo"},
    {"name": "??", "key": "gsk_PPgOa*********pTKm"},
    {"name": "MelLuz201811@gmail.com", "key": "gsk_pXuAEvC4R*********AThMGs6JYJjDi"},
]

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

    if not os.path.exists(GROQ_KEYS_JSON):
        raise RuntimeError("❌ Nenhuma Groq Key inline e arquivo JSON não encontrado.")

    with open(GROQ_KEYS_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    file_keys = extract_valid_keys(data)
    if not file_keys:
        raise RuntimeError("❌ Nenhuma Groq Key válida encontrada no arquivo.")

    print(f"🔑 Groq keys carregadas do arquivo: {len(file_keys)}")
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
                {
                    "role": "system",
                    "content": "You are an English teacher. Return ONLY valid JSON. No markdown.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.4,
        },
        timeout=60,
    )

    response.raise_for_status()
    time.sleep(SLEEP_BETWEEN_CALLS)
    return response.json()["choices"][0]["message"]["content"]

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
        return json.load(f)


def save_vocab_db(db: Dict[str, dict]):
    with open(VOCAB_DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

# ============================================================
# ENRICH TERM
# ============================================================

def enrich_term(term: str) -> dict | None:
    print(f"🌐 Enriquecendo termo: {term}")

    prompt = f"""
For the English term "{term}", return a JSON object with:
- translation_pt
- definition_en
- example_1
- example_2
- common_expressions (array)
"""

    try:
        data = safe_json_parse(call_groq(prompt))
    except Exception as e:
        print(f"⚠️ Falha ao enriquecer '{term}': {e}")
        return None

    return {
        "term": term,
        "translation": data.get("translation_pt", ""),
        "definition": data.get("definition_en", ""),
        "examples": [data.get("example_1", ""), data.get("example_2", "")],
        "expressions": list(dict.fromkeys(data.get("common_expressions", []))),
        "stats": {"seen": 0, "correct": 0, "wrong": 0},
    }

# ============================================================
# ANKI LOGIC
# ============================================================

def weighted_terms(db: Dict[str, dict]) -> List[str]:
    new, wrong, correct = [], [], []

    for term, data in db.items():
        s = data["stats"]
        if s["seen"] == 0:
            new.append(term)
        elif s["wrong"] > s["correct"]:
            wrong.append(term)
        else:
            correct.append(term)

    pool = new * 5 + wrong * 3 + correct
    random.shuffle(pool)
    return pool

# ============================================================
# ANSWER CHECK
# ============================================================

def check_answer(term: str, user_answer: str, correct_translation: str) -> bool:
    prompt = f"""
English term: "{term}"
Correct Portuguese translation:
"{correct_translation}"
User answer:
"{user_answer}"
Is the user's answer correct or equivalent in meaning?
Answer ONLY YES or NO.
"""
    return "YES" in call_groq(prompt).upper()

# ============================================================
# GAME LOOP
# ============================================================

def play(db: Dict[str, dict]):
    print("\n🎮 JOGO DE MEMORIZAÇÃO")
    print("Digite:")
    print(" - tradução → responder")
    print(" - n → não sei (não contabiliza)")
    print(" - s → sair\n")

    while True:
        pool = weighted_terms(db)
        if not pool:
            print("✅ Nenhum termo disponível.")
            return

        term = pool[0]
        entry = db[term]
        stats = entry["stats"]

        print("\n-----------------------------------")
        print(f"🔤 Termo: {term}")
        user = input("✍️ Tradução: ").strip().lower()

        # SAIR
        if user == "s":
            save_vocab_db(db)
            print("💾 Progresso salvo.")
            return

        # NÃO SEI (NÃO CONTABILIZA)
        if user == "n":
            print(f"👉 Tradução: {entry['translation']}")
            input("↩️ ENTER para continuar...")
            continue

        # NORMAL
        correct = check_answer(term, user, entry["translation"])
        stats["seen"] += 1

        if correct:
            stats["correct"] += 1
            print("✅ Correto!")
        else:
            stats["wrong"] += 1
            print("❌ Incorreto.")
            print(f"👉 Correto: {entry['translation']}")

        print(f"📊 Acertos: {stats['correct']} | Erros: {stats['wrong']}")
        input("↩️ ENTER para continuar...")

# ============================================================
# MAIN
# ============================================================

def main():
    vocab_db = load_vocab_db()

    with open(TERMS_SOURCE_JSON, "r", encoding="utf-8") as f:
        terms = json.load(f).get("terms", [])

    for term in terms:
        if term not in vocab_db:
            enriched = enrich_term(term)
            if enriched:
                vocab_db[term] = enriched
                save_vocab_db(vocab_db)

    play(vocab_db)


if __name__ == "__main__":
    main()
