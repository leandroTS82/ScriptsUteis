import json
import random
import math
import os

DEFAULT_TERMS_FILE = r"C:\dev\scripts\ScriptsUteis\Python\english_terms\english_terms.json"


def load_known_terms(
    percentage=0.7,
    max_terms=30,
    seed=42,
    terms_file=DEFAULT_TERMS_FILE,
    verbose=True
):
    """
    Carrega termos já estudados e retorna uma amostra controlada.
    """

    if not os.path.exists(terms_file):
        if verbose:
            print("⚠️ [KnownTerms] english_terms.json não encontrado.")
        return []

    with open(terms_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    terms = data.get("terms", [])
    total = len(terms)

    if total == 0:
        if verbose:
            print("⚠️ [KnownTerms] Nenhum termo encontrado no arquivo.")
        return []

    if seed is not None:
        random.seed(seed)

    sample_size = max(1, math.floor(total * percentage))
    final_size = min(sample_size, max_terms)

    selected = random.sample(terms, final_size)

    # -------------------------------------------------
    # FEEDBACK VISÍVEL
    # -------------------------------------------------
    if verbose:
        print("\n🧠 [KnownTerms] Vocabulário carregado")
        print(f"📄 Arquivo: {terms_file}")
        print(f"📊 Total disponível: {total}")
        print(f"🎯 Percentual alvo: {int(percentage * 100)}%")
        print(f"🔢 Selecionados: {final_size}")
        print("📝 Termos usados como base:")
        for t in selected:
            print(f"   - {t}")
        print("")

    return selected
