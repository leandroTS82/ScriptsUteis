# ============================================================
# anki_english_trainer.py
# Jogo de memorização de inglês estilo Anki + Groq
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

GROQ_KEYS_PATH = r"C:\dev\scripts\ScriptsUteis\Python\secret_tokens_keys\GroqKeys.json"
GROQ_MODEL = "openai/gpt-oss-20b"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

SLEEP_BETWEEN_CALLS = 0.6

# ============================================================
# GROQ
# ============================================================

def load_groq_keys() -> List[str]:
    with open(GROQ_KEYS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [k["key"] for k in data if "key" in k]

GROQ_KEYS = load_groq_keys()

def call_groq(prompt: str) -> str:
    key = random.choice(GROQ_KEYS)

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an English teacher. "
                    "Return ONLY valid JSON. No markdown, no explanations."
                )
            },
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.4
    }

    response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=60)
    response.raise_for_status()

    time.sleep(SLEEP_BETWEEN_CALLS)

    return response.json()["choices"][0]["message"]["content"]

# ============================================================
# JSON ROBUSTO (LLM-PROOF)
# ============================================================

def safe_json_parse(text: str) -> dict:
    """
    Estratégia robusta:
    1. json.loads direto
    2. extração via regex
    """
    text = text.strip()

    # 1️⃣ Tentativa direta (mais confiável)
    try:
        return json.loads(text)
    except Exception:
        pass

    # 2️⃣ Fallback: extrair bloco JSON
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        return json.loads(match.group())

    raise ValueError("Resposta não contém JSON válido.")

# ============================================================
# BANCO DE VOCABULÁRIO
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
# ENRIQUECIMENTO
# ============================================================

def enrich_term(term: str) -> dict:
    print(f"🌐 Enriquecendo termo: {term}")

    prompt = f"""
For the English term "{term}", return a JSON object with:
- translation_pt
- definition_en
- example_1
- example_2
- common_expressions (array)
"""

    raw = call_groq(prompt)

    try:
        data = safe_json_parse(raw)
    except Exception as e:
        print(f"⚠️ Falha ao enriquecer '{term}', pulando termo.")
        print(f"   Motivo: {e}")
        return None

    expressions = list(dict.fromkeys(data.get("common_expressions", [])))

    return {
        "term": term,
        "translation": data.get("translation_pt", ""),
        "definition": data.get("definition_en", ""),
        "examples": [
            data.get("example_1", ""),
            data.get("example_2", "")
        ],
        "expressions": expressions,
        "stats": {
            "seen": 0,
            "correct": 0,
            "wrong": 0
        }
    }

# ============================================================
# PRIORIZAÇÃO (ANKI-LIKE)
# ============================================================

def weighted_terms(db: Dict[str, dict]) -> List[str]:
    new_terms, wrong_terms, correct_terms = [], [], []

    for term, data in db.items():
        s = data["stats"]
        if s["seen"] == 0:
            new_terms.append(term)
        elif s["wrong"] > s["correct"]:
            wrong_terms.append(term)
        else:
            correct_terms.append(term)

    pool = new_terms * 5 + wrong_terms * 3 + correct_terms
    random.shuffle(pool)
    return pool

# ============================================================
# CORREÇÃO SEMÂNTICA
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
# JOGO
# ============================================================

def play(db: Dict[str, dict]):
    print("\n🎮 JOGO DE MEMORIZAÇÃO (s para sair)\n")

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
        user = input("✍️ Tradução: ").strip()

        if user.lower() == "s":
            save_vocab_db(db)
            print("💾 Progresso salvo.")
            return

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
