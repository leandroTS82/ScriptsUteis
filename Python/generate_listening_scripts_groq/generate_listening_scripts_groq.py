"""
===============================================================
 Script: generate_listening_scripts_groq.py
 Autor: Leandro
===============================================================

Gera dois scripts de listening a partir de um JSON:
1) Bilíngue (PT + EN)
2) Immersion Mode (somente EN)

Fonte:
- Traduções e exemplos gerados via GROQ API

Formato de saída:
- Compatível com Google AI Studio Playground (Multi-speaker)

===============================================================
"""

import os
import json
import requests
from datetime import datetime

# ============================================================
# CONFIGURAÇÕES
# ============================================================

GROQ_API_KEY_PATH = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Base\FilesHelper\secret_tokens_keys\groq_api_key.txt"
GROQ_MODEL = "openai/gpt-oss-20b"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

INPUT_JSON = "input.json"  # JSON com chave "pending"
OUTPUT_DIR = "./output"

# ============================================================
# UTILITÁRIOS
# ============================================================

def load_groq_key():
    if not os.path.exists(GROQ_API_KEY_PATH):
        raise FileNotFoundError("Arquivo da API Key da Groq não encontrado.")
    return open(GROQ_API_KEY_PATH, "r", encoding="utf-8").read().strip()

def groq_request(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an English teacher creating natural, simple examples. "
                    "Always respond clearly and objectively."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.4
    }

    response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

# ============================================================
# PROCESSAMENTO DOS TERMOS
# ============================================================

def process_term(term: str) -> dict:
    prompt = f"""
For the English phrase below:

"{term}"

Return EXACTLY in this format:

PT: <natural Brazilian Portuguese meaning>
EX: <very simple, natural example used by a native speaker>

Rules:
- Keep the example short
- Use everyday English
- Do not add explanations
"""
    result = groq_request(prompt)

    pt = ""
    ex = ""

    for line in result.splitlines():
        if line.startswith("PT:"):
            pt = line.replace("PT:", "").strip()
        elif line.startswith("EX:"):
            ex = line.replace("EX:", "").strip()

    return {
        "en": term,
        "pt": pt,
        "example": ex
    }

# ============================================================
# GERADORES DE SCRIPT
# ============================================================

def build_bilingual_script(items: list) -> str:
    lines = [
        "Read aloud in a warm, welcoming tone.\n",
        'Speaker 1:',
        '"Vamos iniciar nosso treinamento de listening em inglês.',
        'Você vai ouvir uma frase em inglês, o significado em português,',
        'e depois um exemplo simples de como um nativo realmente usa essa frase.',
        'Vamos começar?"\n'
    ]

    for item in items:
        lines.extend([
            'Speaker 2:',
            f'"{item["en"]}"\n',
            'Speaker 1:',
            f'"{item["pt"]}"\n',
            'Speaker 2:',
            f'"{item["example"]}"\n'
        ])

    lines.extend([
        'Speaker 1:',
        '"Ouça novamente e tente repetir em voz alta. Isso vai melhorar sua escuta."'
    ])

    return "\n".join(lines)

def build_immersion_script(items: list) -> str:
    lines = [
        "Read aloud in a calm, natural tone and bit slowly.\n",
        'Speaker 1:',
        '"Welcome to your English listening practice.',
        'Listen carefully and focus on natural pronunciation."\n'
    ]

    for item in items:
        lines.extend([
            'Speaker 2:',
            f'"{item["en"]}"\n',
            'Speaker 2:',
            f'"{item["example"]}"\n'
        ])

    lines.extend([
        'Speaker 1:',
        '"Great job. Listen again and try to repeat naturally."'
    ])

    return "\n".join(lines)

# ============================================================
# EXECUÇÃO PRINCIPAL
# ============================================================

def main():
    global GROQ_API_KEY
    GROQ_API_KEY = load_groq_key()

    if not os.path.exists(INPUT_JSON):
        raise FileNotFoundError("Arquivo input.json não encontrado.")

    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    terms = data.get("pending", [])
    if not terms:
        raise ValueError("Nenhum termo encontrado em 'pending'.")

    print(f"🔍 Processando {len(terms)} termos...")

    processed = []
    for term in terms:
        print(f"➡ {term}")
        processed.append(process_term(term))

    timestamp = datetime.now().strftime("%y%m%d%H%M")
    ensure_dir(OUTPUT_DIR)

    bilingual_path = os.path.join(
        OUTPUT_DIR, f"{timestamp}_scriptBILINGUE.txt"
    )
    immersion_path = os.path.join(
        OUTPUT_DIR, f"{timestamp}_scriptIMMERSIONMODE.txt"
    )

    with open(bilingual_path, "w", encoding="utf-8") as f:
        f.write(build_bilingual_script(processed))

    with open(immersion_path, "w", encoding="utf-8") as f:
        f.write(build_immersion_script(processed))

    print("\n✅ Scripts gerados com sucesso:")
    print("📄", bilingual_path)
    print("📄", immersion_path)

# ============================================================

if __name__ == "__main__":
    main()
