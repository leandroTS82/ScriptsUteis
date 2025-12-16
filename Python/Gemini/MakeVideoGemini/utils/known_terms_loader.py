import json
import os
import random
import math
import re
import time
from utils.term_translator import translate_to_english
from utils.term_ranker import rank_terms_by_relevance

DEFAULT_TERMS_FILE = r"C:\dev\scripts\ScriptsUteis\Python\english_terms\english_terms.json"


def is_probably_portuguese(text: str) -> bool:
    return bool(re.search(r"[ãõçáéíóúàêô]", text.lower()))


def normalize_term(term: str) -> str:
    term = term.lower().strip()
    term = re.sub(r"[^\w\s']", "", term)
    return term


def load_known_terms(
    target_word: str,
    percentage=0.8,
    max_terms=60,
    terms_file=DEFAULT_TERMS_FILE,
    verbose=True
):
    if not os.path.exists(terms_file):
        if verbose:
            print("⚠️ [KnownTerms] english_terms.json não encontrado.")
        return []

    with open(terms_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    raw_terms = data.get("terms", [])
    if not raw_terms:
        if verbose:
            print("⚠️ [KnownTerms] Nenhum termo encontrado.")
        return []

    # -----------------------------
    # Seed dinâmica (por palavra)
    # -----------------------------
    daily_seed = hash(target_word.lower()) + int(time.time() // 86400)
    random.seed(daily_seed)

    normalized_terms = []

    for t in raw_terms:
        original = t.strip()

        if is_probably_portuguese(original):
            original = translate_to_english(original)

        norm = normalize_term(original)
        if norm:
            normalized_terms.append(norm)

    # -----------------------------
    # Ranking semântico
    # -----------------------------
    ranked = rank_terms_by_relevance(
        target_word=target_word,
        terms=normalized_terms,
        top_k=200  # corta antes de randomizar
    )

    total = len(ranked)
    sample_size = max(1, math.floor(total * percentage))
    final_size = min(sample_size, max_terms)

    selected = random.sample(ranked, final_size)

    if verbose:
        print("\n🧠 [KnownTerms] Vocabulário carregado (inteligente)")
        print(f"🎯 Palavra-alvo: {target_word}")
        print(f"📊 Total analisado: {len(raw_terms)}")
        print(f"🔢 Selecionados: {final_size}")
        print("📝 Termos priorizados:")
        for t in selected:
            print(f"   - {t}")
        print("")

    return selected
