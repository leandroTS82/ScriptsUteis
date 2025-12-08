"""
====================================================================================
 Script: mainTranscript.py (Groq + Gemini Hybrid + Correção Ortográfica + Níveis)
 Funções:
   - Corrigir ortografia em PT ou EN
   - Traduzir PT → EN obrigatoriamente
   - Corrigir inglês com erros
   - Gerar definição PT + exemplos EN conforme níveis configurados
   - Preview colorido
   - Explicar motivo do erro/correção
   - Indicador de modelo usado
   - Registrar CreateLater.json (sem ponto final)
   - Registrar TranscriptResults.json
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
GROQ_KEY_FILE = "../Groq/groq_api_key.txt"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b"

GEMINI_KEY_PATH = "../Gemini/google-gemini-key.txt"
GEMINI_MODEL = "gemini-2.0-flash"

LEVELS_FILE = "./levels.json"
CREATE_LATER = "./CreateLater.json"
FULL_RESULTS = "./TranscriptResults.json"

genai.configure(api_key=open(GEMINI_KEY_PATH, "r").read().strip())


# ================================================================================
# HELPERS
# ================================================================================
def sanitize_sentence(s):
    return s.rstrip(".!? ").strip()


def safe_json_dump(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_groq_key():
    return open(GROQ_KEY_FILE, "r", encoding="utf-8").read().strip()


def load_levels():
    if not os.path.exists(LEVELS_FILE):
        return {"A2": True, "B1": True, "B2": True}
    return json.load(open(LEVELS_FILE, "r", encoding="utf-8"))


# ================================================================================
# SAVE CreateLater.json
# ================================================================================
def save_create_later(item):
    item = sanitize_sentence(item)
    if not os.path.exists(CREATE_LATER):
        safe_json_dump(CREATE_LATER, {"pending": [item]})
        print(f"📌 CreateLater.json criado com: {item}")
        return

    data = json.load(open(CREATE_LATER, "r", encoding="utf-8"))
    if item not in data["pending"]:
        data["pending"].append(item)
        safe_json_dump(CREATE_LATER, data)
        print(f"📌 Adicionado ao CreateLater.json: {item}")


# ================================================================================
# SAVE TranscriptResults.json
# ================================================================================
def save_transcript_result(palavra, definicao, exemplos):
    entry = {
        "palavra_chave": palavra,
        "definicao_pt": definicao,
        "exemplos": exemplos
    }

    if not os.path.exists(FULL_RESULTS):
        safe_json_dump(FULL_RESULTS, [entry])
        print("📚 TranscriptResults.json criado!")
        return

    data = json.load(open(FULL_RESULTS, "r", encoding="utf-8"))
    data.append(entry)
    safe_json_dump(FULL_RESULTS, data)
    print("📚 Conteúdo registrado em TranscriptResults.json")


# ================================================================================
# 1️⃣ — CORRIGIR ORTOGRAFIA + TRADUZIR → EN (GROQ)
# ================================================================================
def groq_correct_and_translate(text):
    prompt = f"""
Tasks:
1. Correct misspellings in Portuguese or English.
2. If text is Portuguese → translate to natural English.
3. If mixed PT/EN → translate PT parts and fix English grammar.
4. If English is incorrect → fix grammar.
5. ALWAYS return English in "corrected".

Return ONLY JSON:
{{
 "corrected": "final English sentence",
 "had_error": true/false,
 "reason": "short explanation"
}}

Input: "{text}"
"""
    headers = {"Authorization": f"Bearer {load_groq_key()}", "Content-Type": "application/json"}
    payload = {"model": GROQ_MODEL, "messages": [{"role": "user", "content": prompt}]}

    try:
        res = requests.post(GROQ_URL, json=payload, headers=headers, timeout=12)
        res.raise_for_status()
        raw = res.json()["choices"][0]["message"]["content"]
        data = json.loads(raw[raw.find("{"): raw.rfind("}") + 1])
        data["model_used"] = "Groq"
        return data
    except:
        return None


# ================================================================================
# 1️⃣ — CORRIGIR ORTOGRAFIA + TRADUZIR → EN (GEMINI)
# ================================================================================
def gemini_correct_and_translate(text):
    prompt = f"""
You MUST ALWAYS output English.

Tasks:
1. Fix misspellings (PT or EN).
2. If Portuguese → translate to English.
3. If English → fix grammar.
4. If mixed → translate PT parts and fix grammar.

Return ONLY JSON:
{{
 "corrected": "final English result",
 "had_error": true/false,
 "reason": "short explanation"
}}

Input: "{text}"
"""
    model = genai.GenerativeModel(GEMINI_MODEL)
    raw = model.generate_content(prompt).text
    data = json.loads(raw[raw.find("{"): raw.rfind("}") + 1])
    data["model_used"] = "Gemini"
    return data


# ================================================================================
# 2️⃣ — GERAR DEFINIÇÃO + EXEMPLOS (A2/B1/B2 configuráveis)
# ================================================================================
def generate_wordbank(corrected_sentence, force_gemini=False):

    levels = load_levels()
    examples_json = []

    if levels.get("A2"):
        examples_json.append({"level": "A2", "phrase": "..."})
    if levels.get("B1"):
        examples_json.append({"level": "B1", "phrase": "..."})
    if levels.get("B2"):
        examples_json.append({"level": "B2", "phrase": "..."})

    prompt = f"""
Crie o seguinte JSON:

{{
 "definition_pt": "uma explicação natural, curta e clara do significado da expressão",
 "examples": {json.dumps(examples_json, ensure_ascii=False)}
}}

REGRAS DA DEFINIÇÃO:
- Explique claramente o significado de "{corrected_sentence}".
- A explicação deve ser clara e natural.
- NÃO repita a frase inteira no começo.
- NÃO traduza literalmente; explique o sentido.

REGRAS DOS EXEMPLOS:
- Todas as frases devem ser SENTENÇAS completas em inglês.
- Todas devem incluir EXACTAMENTE: "{corrected_sentence}"
- A2 → simples e curta.
- B1 → com contexto.
- B2 → mais detalhada e fluida.
- Não retornar a expressão isolada.

Retorne SOMENTE o JSON.
"""

    try:
        if not force_gemini:
            headers = {"Authorization": f"Bearer {load_groq_key()}", "Content-Type": "application/json"}
            payload = {"model": GROQ_MODEL, "messages": [{"role": "user", "content": prompt}]}
            res = requests.post(GROQ_URL, json=payload, headers=headers)
            res.raise_for_status()
            raw = res.json()["choices"][0]["message"]["content"]
            model_used = "Groq"
        else:
            raise Exception()
    except:
        model = genai.GenerativeModel(GEMINI_MODEL)
        raw = model.generate_content(prompt).text
        model_used = "Gemini"

    data = json.loads(raw[raw.find("{"): raw.rfind("}") + 1])
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
        print(f"{C_RED}A frase “{original}” estava incorreta.{C_RESET}")
        print(f"{C_YELLOW}Motivo: {reason}{C_RESET}")
        print(f"{C_GREEN}Forma corrigida/traduzida: {corrected}{C_RESET}\n")
    else:
        print(f"{C_GREEN}Nenhum erro encontrado.{C_RESET}")
        print(f"{C_GREEN}Resultado final: {corrected}{C_RESET}\n")

    print(f"{C_BLUE}Palavra-chave: {corrected}{C_RESET}")
    print(f"{C_YELLOW}📘 Definição PT:{C_RESET} {definition_pt}\n")

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

    # 1 — CORRIGIR ORTOGRAFIA + TRADUZIR
    result = (
        gemini_correct_and_translate(original)
        if force_gemini
        else (groq_correct_and_translate(original) or gemini_correct_and_translate(original))
    )

    corrected = sanitize_sentence(result["corrected"])
    had_error = result["had_error"]
    reason = result["reason"]
    model_used = result["model_used"]

    # 2 — SALVAR CreateLater
    save_create_later(corrected)

    # 3 — DEFINIÇÃO + EXEMPLOS
    data = generate_wordbank(corrected, force_gemini)
    definicao = data["definition_pt"]
    exemplos = data["examples"]

    # 4 — PREVIEW
    print_preview(original, corrected, had_error, reason, definicao, exemplos, model_used)

    # 5 — SALVAR resultado completo
    save_transcript_result(corrected, definicao, exemplos)


if __name__ == "__main__":
    main()
