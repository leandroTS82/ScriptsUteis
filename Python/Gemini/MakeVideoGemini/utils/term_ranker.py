import re


def tokenize(text: str):
    return set(re.findall(r"\b\w+\b", text.lower()))


def score_term(target_tokens, term: str) -> int:
    term_tokens = tokenize(term)
    shared = target_tokens & term_tokens
    return len(shared)


def rank_terms_by_relevance(target_word: str, terms: list, top_k=200):
    target_tokens = tokenize(target_word)

    scored = []
    for t in terms:
        score = score_term(target_tokens, t)
        if score > 0:
            scored.append((score, t))

    scored.sort(reverse=True, key=lambda x: x[0])

    ranked = [t for _, t in scored]

    # fallback: se nada relacionado, retorna tudo
    return ranked[:top_k] if ranked else terms[:top_k]
