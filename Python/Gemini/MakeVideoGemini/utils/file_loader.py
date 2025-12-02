import os
import json

def ensure_dir(path: str):
    """Cria diretórios caso não existam."""
    os.makedirs(path, exist_ok=True)

def load_json(path: str):
    """Carrega JSON com segurança."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path: str, data):
    """Salva JSON formatado com indentação."""
    ensure_dir(os.path.dirname(path))

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_text(path: str):
    """Carrega arquivo de texto simples."""
    if not os.path.exists(path):
        return None

    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()

def save_text(path: str, text: str):
    """Salva texto."""
    ensure_dir(os.path.dirname(path))

    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
