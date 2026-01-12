import json
import os
from datetime import datetime

OUTPUT_DIR = "./output"
ENRICHED_JSON = os.path.join(OUTPUT_DIR, "english_enriched.json")
FLAT_JSON = os.path.join(OUTPUT_DIR, "english_terms_flat.json")


def _normalize_item(item: dict) -> dict:
    """
    Normaliza qualquer variação retornada pelo LLM
    garantindo a chave 'text'
    """

    # Caso ideal
    if "text" in item and isinstance(item["text"], str):
        item["text"] = item["text"].strip()
        return item

    # Campos possíveis retornados por LLMs
    CANDIDATE_KEYS = (
        "term",
        "chunk",
        "expression",
        "discourse_marker",
        "marker",
        "word",
        "phrase"
    )

    for key in CANDIDATE_KEYS:
        if key in item and isinstance(item[key], str):
            item["text"] = item[key].strip()
            return item

    # Fallback extremo: primeiro string do dict
    for value in item.values():
        if isinstance(value, str):
            item["text"] = value.strip()
            return item

    # Último recurso (não quebra o fluxo)
    item["text"] = json.dumps(item, ensure_ascii=False)
    return item


def _unique_merge(existing: list, incoming: list) -> list:
    index = {}

    for item in existing:
        norm = _normalize_item(item)
        index[norm["text"].lower()] = norm

    for item in incoming:
        norm = _normalize_item(item)
        key = norm["text"].lower()
        if key not in index:
            index[key] = norm

    return list(index.values())


def save_enriched(data: dict):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if os.path.exists(ENRICHED_JSON):
        with open(ENRICHED_JSON, "r", encoding="utf-8") as f:
            stored = json.load(f)
    else:
        stored = {
            "source": "english_extractor",
            "generated_at": "",
            "items": {
                "terms": [],
                "chunks": [],
                "expressions": [],
                "discourse_markers": []
            }
        }

    for category in stored["items"]:
        stored["items"][category] = _unique_merge(
            stored["items"][category],
            data.get(category, [])
        )

    stored["generated_at"] = datetime.now().isoformat()

    with open(ENRICHED_JSON, "w", encoding="utf-8") as f:
        json.dump(stored, f, ensure_ascii=False, indent=2)


def generate_flat_terms():
    if not os.path.exists(ENRICHED_JSON):
        raise FileNotFoundError("english_enriched.json não encontrado")

    with open(ENRICHED_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    seen = set()
    flat = []

    for items in data["items"].values():
        for item in items:
            norm = _normalize_item(item)
            key = norm["text"].lower()
            if key not in seen:
                seen.add(key)
                flat.append({"term": norm["text"]})

    with open(FLAT_JSON, "w", encoding="utf-8") as f:
        json.dump(flat, f, ensure_ascii=False, indent=2)
