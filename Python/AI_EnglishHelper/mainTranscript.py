"""
====================================================================================
 Script: mainTranscript.py (Groq + Gemini Hybrid + Registro Estendido)
 Funções:
   - Detectar idioma e traduzir PT → EN corrigindo ortografia
   - Corrigir inglês errado
   - Gerar definição PT + 3 exemplos EN (A2, B1, B2)
   - Exemplos obrigatoriamente frases completas
   - Preview colorido
   - Explicar motivo do erro
   - Indicar modelo utilizado (Groq ou Gemini)
   - Registrar frase corrigida no CreateLater.json (sem ponto final)
   - Registrar resultado em TranscriptResults.json
   - Groq → fallback Gemini → forçar Gemini com -Gemini
====================================================================================
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
OUTPUT_FULL_RESULTS = "./TranscriptResults.json"

genai.configure(api_key=open(GEMINI_KEY_PATH, "r").read().strip())


# ================================================================================
# HELPERS
# ================================================================================
def sanitize_sentence(s: str) -> str:
    """Remove trailing punctuation and trim whitespace."""
    return s.rstrip(".!? ").strip()


def safe_json_dump(path, data):
    """Save JSON with proper unicode."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_groq_key():
    return open(GROQ_API_KEY_FILE, "r", encoding="utf-8").read().strip()


# ================================================================================
# SAVE CreateLater.json
# ================================================================================
def save_create_later(item):
    item = sanitize_sentence(item)

    if not os.path.exists(OUTPUT_CREATE_LATER):
        safe_json_dump(OUTPUT_CREATE_LATER, {"pending": [item]})
        print(f"📌 CreateLater.json criado com: {item}")
        return

    data = json.load(open(OUTPUT_CREATE_LATER, "r", encoding="utf-8"))
    if item not in data["pending"]:
        data["pending"].append(item)
        safe_json_dump(OUTPUT_CREATE_LATER, data)
        print(f"📌 Adicionado ao CreateLater.json: {item}")


# ================================================================================
# SAVE TranscriptResults.json (novo recurso)
# ================================================================================
def save_transcript_result(palavra, definicao, exemplos):
    entry = {
        "palavra_chave": palavra,
        "definicao_pt": definicao,
        "exemplos": exemplos
    }

    if not os.path.exists(OUTPUT_FULL_RESULTS):
        safe_json_dump(OUTPUT_FULL_RESULTS, [entry])
        print("📚 TranscriptResults.json criado!")
        return

    data = json.load(open(OUTPUT_FULL_RESULTS, "r", encoding="utf-8"))
    data.append(entry)
    safe_json_dump(OUTPUT_FULL_RESULTS, data)
    print("📚 Conteúdo registrado em TranscriptResults.json")


# ================================================================================
# TRANSLATE + FIX (GROQ)
# ================================================================================
def groq_translate_fix(text):
    prompt = f"""
Analyze the input. It may contain Portuguese or incorrect English.

Return ONLY JSON:
{{
 "corrected": "...",
 "had_error": true/false,
 "reason": "short explanation"
}}
Input: "{text}"
"""

    payload = {"model": GROQ_MODEL, "messages": [{"role": "user", "content": prompt}]}
    headers = {"Authorization": f"Bearer {load_groq_key()}", "Content-Type": "application/json"}

    try:
        resp = requests.post(GROQ_URL, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"]
        data = json.loads(raw[raw.find("{"):raw.rfind("}") + 1])
        data["model_used"] = "Groq"
        return data
    except Exception:
        return None


# ================================================================================
# TRANSLATE + FIX (GEMINI)
# ================================================================================
def gemini_translate_fix(text):
    prompt = f"""
Translate if needed, fix grammar, return only JSON:
{{
 "corrected": "...",
 "had_error": true/false,
 "reason": "short explanation"
}}
Input: "{text}"
"""

    model = genai.GenerativeModel(GEMINI_MODEL)
    raw = model.generate_content(prompt).text
    data = json.loads(raw[raw.find("{"):raw.rfind("}") + 1])
    data["model_used"] = "Gemini"
    return data


# ================================================================================
# EXPLANATION + EXAMPLES (A2/B1/B2)
# ================================================================================
def generate_wordbank_data(corrected_sentence, force_gemini=False):
    prompt = f"""
Create JSON:
{{
 "definition_pt": "...",
 "examples": [
   {{"level": "A2", "phrase": "..." }},
   {{"level": "B1", "phrase": "..." }},
   {{"level": "B2", "phrase": "..." }}
 ]
}}

RULES:
- All 3 examples must be FULL sentences (subject + verb + complement)
- Each example MUST include the phrase verbatim: "{corrected_sentence}"
- The sentence CANNOT be just the phrase alone
- A2 sentence must be simple and short
- B1 sentence must add context
- B2 sentence must expand meaning naturally
- All examples MUST be in English
"""

    try:
        if not force_gemini:
            payload = {"model": GROQ_MODEL, "messages": [{"role": "user", "content": prompt}]}
            headers = {"Authorization": f"Bearer {load_groq_key()}", "Content-Type": "application/json"}
            resp = requests.post(GROQ_URL, json=payload, headers=headers)
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"]
            model_used = "Groq"
        else:
            raise Exception()

    except:
        model = genai.GenerativeModel(GEMINI_MODEL)
        raw = model.generate_content(prompt).text
        model_used = "Gemini"

    data = json.loads(raw[raw.find("{"):raw.rfind("}") + 1])
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
        print("Uso: python mainTranscript.py \"frase\"")
        print("     python mainTranscript.py -Gemini \"frase\"")
        return

    force_gemini = sys.argv[1] == "-Gemini"
    original = " ".join(sys.argv[2:] if force_gemini else sys.argv[1:]).strip()

    print("🔍 Processando:", original)

    # 1) TRADUZIR / CORRIGIR
    result = gemini_translate_fix(original) if force_gemini else (groq_translate_fix(original) or gemini_translate_fix(original))

    corrected = result["corrected"]
    had_error = result["had_error"]
    reason = result["reason"]
    model_used = result["model_used"]

    # 2) SALVAR CreateLater.json
    save_create_later(corrected)

    # 3) GERAR EXPLICAÇÃO + EXEMPLOS
    data = generate_wordbank_data(corrected, force_gemini)
    definicao = data["definition_pt"]
    exemplos = data["examples"]

    # 4) PREVIEW
    print_preview(original, corrected, had_error, reason, definicao, exemplos, model_used)

    # 5) SALVAR TranscriptResults.json
    save_transcript_result(corrected, definicao, exemplos)


if __name__ == "__main__":
    main()
