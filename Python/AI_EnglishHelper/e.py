import sys
import json
import requests
from itertools import cycle

# =====================================================================
# GROQ CONFIG — MULTI KEY (INLINE)
# =====================================================================

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b"

GROQ_KEYS = [
    {"name": "lts@gmail.com", "key": "gsk_r***"},
    {"name": "ltsCV@gmail", "key": "gsk_4***"},
    {"name": "butterfly", "key": "gsk_n***"},
    {"name": "??", "key": "gsk_P***"},
    {"name": "MelLuz201811@gmail.com", "key": "gsk_***i"}
]

key_cycle = cycle(GROQ_KEYS)

# =====================================================================
# GROQ CALL (ROTATION)
# =====================================================================

def call_groq(prompt: str) -> dict:
    key_info = next(key_cycle)

    headers = {
        "Authorization": f"Bearer {key_info['key']}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2
    }

    res = requests.post(GROQ_URL, json=payload, headers=headers, timeout=30)
    res.raise_for_status()

    raw = res.json()["choices"][0]["message"]["content"]
    json_text = raw[raw.find("{"): raw.rfind("}") + 1]
    obj = json.loads(json_text)
    obj["_key_used"] = key_info["name"]

    return obj

# =====================================================================
# PROMPT BUILDER — PREVIEW ENRIQUECIDO
# =====================================================================

def build_prompt(term: str, context: str) -> str:
    return f"""
You are a senior English teacher helping a Brazilian student build ACTIVE English.

Goal:
- Connect logical and emotional journey
- Describe an environment step by step in Portuguese
- Transfer that idea into natural English
- Improve the sentence gradually
- Teach grammar by usage, not theory

Context so far:
{context}

Input concept or sentence:
"{term}"

Return ONLY JSON with the structure below.

{{
  "corrected_sentence": "...",
  "why_this_is_better": "...",
  "grammar_focus": "...",
  "timeline": {{
    "present_positive": "...",
    "present_negative": "...",
    "past_positive": "...",
    "past_negative": "...",
    "future_positive": "...",
    "future_negative": "...",
    "question_positive": "...",
    "question_negative": "..."
  }},
  "learning_tip_pt": "Dica curta em português para melhorar o inglês ativo"
}}

Rules:
- Be clear, simple, natural
- Use descriptive language
- Keep emotional + logical coherence
- Do NOT explain grammar academically
- Teach by contrast and examples
"""

# =====================================================================
# PREVIEW RENDER
# =====================================================================

def render_preview(data: dict):
    print("\n════════════════════════════════════════")
    print("        PREVIEW ENRIQUECIDO")
    print("════════════════════════════════════════\n")

    print(f"Key usada: {data.get('_key_used')}\n")

    print("Frase melhorada:")
    print(f"  {data['corrected_sentence']}\n")

    print("Por que ficou melhor:")
    print(f"  {data['why_this_is_better']}\n")

    print("Foco gramatical prático:")
    print(f"  {data['grammar_focus']}\n")

    print("Linha do tempo verbal:\n")
    for k, v in data["timeline"].items():
        print(f"  {k.replace('_', ' ').title():<25}: {v}")

    print("\nDica para inglês ativo:")
    print(f"  {data['learning_tip_pt']}")

    print("\n════════════════════════════════════════\n")

# =====================================================================
# MAIN LOOP
# =====================================================================

def main():
    context = ""
    current_term = None

    while True:
        if not current_term:
            current_term = input("Digite o termo/frase inicial: ").strip()
            if not current_term:
                print("Encerrando.")
                return

        prompt = build_prompt(current_term, context)
        result = call_groq(prompt)

        render_preview(result)

        context += f"\n{result['corrected_sentence']}"

        action = input(
            "\nDigite:\n"
            "m = gerar outro preview diferente (mesmo termo)\n"
            "s = sair\n"
            "ou digite o próximo termo: "
        ).strip().lower()

        if action == "s":
            print("Encerrando.")
            break
        elif action == "m":
            continue
        else:
            current_term = action

if __name__ == "__main__":
    main()
