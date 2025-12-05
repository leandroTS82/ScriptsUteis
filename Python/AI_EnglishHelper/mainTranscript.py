"""
====================================================================================
 Script: mainTranscript.py (Groq + Gemini Hybrid)
 Funções:
   - Detectar idioma e traduzir PT → EN corrigindo ortografia
   - Corrigir inglês errado
   - Gerar definição PT + exemplos EN (A2, B1, B2)
   - Preview colorido extremamente limpo
   - Explicar rapidamente o motivo do erro
   - Exibir modelo utilizado (Groq ou Gemini)
   - Registrar frase corrigida no CreateLater.json (sem ponto final)
   - EXECUÇÃO INTELIGENTE:
         ✔ Primeiro tenta GROQ
         ✔ Se Groq falhar → fallback para GEMINI
         ✔ Flag -Gemini → força uso do Gemini
====================================================================================
Python mainTranscript.py ""

"""

import os
import sys
import json
import requests
import google.generativeai as genai


# ================================================================================
# CONFIG
# ================================================================================
GROQ_API_KEY_FILE = "../Groq/groq_api_key.txt"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b"

GEMINI_KEY_PATH = "../Gemini/google-gemini-key.txt"
GEMINI_MODEL = "gemini-2.0-flash"

OUTPUT_CREATE_LATER = "./CreateLater.json"

# Gemini key
genai.configure(api_key=open(GEMINI_KEY_PATH, "r").read().strip())


# ================================================================================
# HELPERS
# ================================================================================
def sanitize_sentence(s):
    """Remove trailing punctuation when saving to CreateLater.json"""
    return s.rstrip(".!? ").strip()


def load_groq_key():
    return open(GROQ_API_KEY_FILE, "r", encoding="utf-8").read().strip()


def save_create_later(item):
    item = sanitize_sentence(item)

    if not os.path.exists(OUTPUT_CREATE_LATER):
        json.dump({"pending": [item]}, open(OUTPUT_CREATE_LATER, "w"), indent=2)
        print(f"📌 CreateLater.json criado com: {item}")
        return

    data = json.load(open(OUTPUT_CREATE_LATER, "r"))

    if item not in data["pending"]:
        data["pending"].append(item)
        json.dump(data, open(OUTPUT_CREATE_LATER, "w"), indent=2)
        print(f"📌 Adicionado ao CreateLater.json: {item}")


# ================================================================================
# TRANSLATE + FIX (GROQ)
# ================================================================================
def groq_translate_fix(text):
    prompt = f"""
Analyze the following sentence. It may contain:
- Portuguese
- incorrect English
- or mixed PT/EN.

Tasks:
1. Translate PT → EN if needed.
2. Fix all grammar if needed.
3. Return ONLY this JSON:
{{
 "corrected": "...",
 "had_error": true/false,
 "reason": "quick explanation of the error in 1 short sentence"
}}

Respond ONLY with JSON.
Input: "{text}"
"""

    payload = {"model": GROQ_MODEL, "messages": [{"role": "user", "content": prompt}]}

    headers = {
        "Authorization": f"Bearer {load_groq_key()}",
        "Content-Type": "application/json"
    }

    try:
        resp = requests.post(GROQ_URL, json=payload, headers=headers, timeout=12)
        resp.raise_for_status()
        msg = resp.json()["choices"][0]["message"]["content"]

        msg_clean = msg[msg.find("{"):msg.rfind("}") + 1]
        data = json.loads(msg_clean)
        data["model_used"] = "Groq"
        return data
    except Exception:
        return None


# ================================================================================
# TRANSLATE + FIX (GEMINI)
# ================================================================================
def gemini_translate_fix(text):
    prompt = f"""
Analyze the following sentence that may contain Portuguese or incorrect English.

Tasks:
1. Translate PT → EN if needed.
2. Fix grammar.
3. Return ONLY this JSON:
{{
 "corrected": "...",
 "had_error": true/false,
 "reason": "quick explanation of why the input was incorrect"
}}

Input: "{text}"
"""

    model = genai.GenerativeModel(GEMINI_MODEL)
    resp = model.generate_content(prompt)

    msg = resp.text.strip()
    msg_clean = msg[msg.find("{"):msg.rfind("}") + 1]

    data = json.loads(msg_clean)
    data["model_used"] = "Gemini"
    return data


# ================================================================================
# EXPLANATION + EXAMPLES (A2/B1/B2)
# ================================================================================
def generate_wordbank_data(corrected_sentence, force_gemini=False):
    prompt = f"""
Create a WordBank-style JSON for the English phrase:
"{corrected_sentence}"

Return ONLY this JSON:
{{
  "definition_pt": "explicação NATURAL em português explicando o significado",
  "examples": [
    {{"level": "A2", "phrase": "..." }},
    {{"level": "B1", "phrase": "..." }},
    {{"level": "B2", "phrase": "..." }}
  ]
}}

RULES:
- All examples MUST be in English.
- Must use EXACT phrase: {corrected_sentence}
- No comments, no markdown.
"""

    if force_gemini:
        model = genai.GenerativeModel(GEMINI_MODEL)
        raw = model.generate_content(prompt).text
    else:
        try:
            payload = {"model": GROQ_MODEL, "messages": [{"role": "user", "content": prompt}]}
            headers = {
                "Authorization": f"Bearer {load_groq_key()}",
                "Content-Type": "application/json"
            }
            resp = requests.post(GROQ_URL, json=payload, headers=headers)
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"]
            model_used = "Groq"
        except:
            model = genai.GenerativeModel(GEMINI_MODEL)
            raw = model.generate_content(prompt).text
            model_used = "Gemini"

    json_clean = raw[raw.find("{"):raw.rfind("}") + 1]
    data = json.loads(json_clean)
    data["model_used"] = model_used
    return data


# ================================================================================
# PREVIEW COLORIDO
# ================================================================================
def print_preview(original, corrected, had_error, reason, definition_pt, examples, model):
    C_RESET = "\033[0m"
    C_RED = "\033[91m"
    C_GREEN = "\033[92m"
    C_BLUE = "\033[94m"
    C_YELLOW = "\033[93m"
    C_TITLE = "\033[96m\033[1m"

    print(f"\n{C_TITLE}══════════════════════════════════════")
    print(f"           PREVIEW DO TRANSCRIPT")
    print(f"══════════════════════════════════════{C_RESET}\n")

    print(f"🔧 Modelo usado: {model}\n")

    if had_error:
        print(f"{C_RED}A frase “{original}” está incorreta.{C_RESET}")
        print(f"{C_YELLOW}Motivo: {reason}{C_RESET}")
        print(f"{C_GREEN}Forma correta: {corrected}{C_RESET}\n")
    else:
        print(f"{C_GREEN}A frase está correta!{C_RESET}\n")

    print(f"{C_BLUE}Palavra-chave: {corrected}{C_RESET}")
    print(f"{C_YELLOW}📘 Definição PT: {definition_pt}{C_RESET}\n")

    print(f"{C_BLUE}Exemplos:{C_RESET}")
    for ex in examples:
        print(f"   ➜ ({ex['level']}) {ex['phrase']}")
    print()


# ================================================================================
# MAIN
# ================================================================================
def main():
    if len(sys.argv) < 2:
        print("Uso: python mainTranscript.py \"frase aqui\"")
        print("     python mainTranscript.py -Gemini \"frase\"")
        return

    force_gemini = sys.argv[1] == "-Gemini"
    original = " ".join(sys.argv[2:] if force_gemini else sys.argv[1:])

    print("🔍 Processando:", original)

    # 1) Tradução + correção
    if force_gemini:
        result = gemini_translate_fix(original)
    else:
        result = groq_translate_fix(original)
        if result is None:
            print("⚠️ Groq falhou, alternando para Gemini…")
            result = gemini_translate_fix(original)

    corrected = result["corrected"]
    had_error = result["had_error"]
    reason = result.get("reason", "grammar issue")
    model_used = result["model_used"]

    # 2) Registrar CreateLater.json
    save_create_later(corrected)

    # 3) Gerar exemplos + definição
    data = generate_wordbank_data(corrected, force_gemini)

    # 4) Preview
    print_preview(original, corrected, had_error, reason,
                  data["definition_pt"], data["examples"], model_used)


if __name__ == "__main__":
    main()
