import json
import os

def load_state(path: str) -> dict:
    """
    Carrega o estado de execução.
    Seguro contra:
    - arquivo inexistente
    - arquivo vazio
    - JSON corrompido
    """
    if not os.path.exists(path):
        return {}

    if os.path.getsize(path) == 0:
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_state(path: str, state: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def is_processed(state: dict, slug: str) -> bool:
    return state.get(slug, False)

def mark_processed(state: dict, slug: str) -> None:
    state[slug] = True
