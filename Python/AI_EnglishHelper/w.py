"""
====================================================================================
 Script: mainTranscript.py (Groq Only)
 Versão: Ultra otimizada — Apenas Groq (sem Gemini)
 Funções:
   - Corrigir ortografia (PT/EN)
   - Traduzir PT → EN obrigatoriamente
   - Corrigir inglês com erros
   - Gerar definição PT + exemplos EN conforme levels internos
   - Exemplos seguem tamanho: short/medium/long
   - Preview colorido
   - Registro em CreateLater.json e TranscriptResults.json
   - Solicita input se nenhum termo for passado via CLI
   - Loop interativo: repetir processo e gerar PDF via doc.py
====================================================================================
python mainTranscript.py "frase"
python mainTranscript.py
"""

import os
import sys
import json
import requests
import random
from itertools import cycle
from datetime import datetime

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
from groq_keys_loader import GROQ_KEYS
# ================================================================================
# CONFIG - GROQ MULTI KEYS (ROTATION / RANDOM)
# ================================================================================



_groq_key_cycle = cycle(random.sample(GROQ_KEYS, len(GROQ_KEYS)))

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b"

# ================================================================================
# PATHS
# ================================================================================

current_date = datetime.now().strftime('%Y%m%d')

CREATE_LATER = f"./CreateLater/CreateLater_{current_date}.json"
FULL_RESULTS = "./TranscriptResults.json"

EXTERNAL_TERMS_PATH = r"C:\dev\scripts\ScriptsUteis\Python\english_terms\english_terms.json"

LEVELS = {
    "A1": {"enabled": False, "size": "short"},
    "A2": {"enabled": True,  "size": "medium"},
    "B1": {"enabled": True,  "size": "medium"},
    "B2": {"enabled": True,  "size": "medium"},
    "C1": {"enabled": False, "size": "long"},
    "C2": {"enabled": False, "size": "long"}
}

# ================================================================================
# HELPERS
# ================================================================================

def sanitize_sentence(s: str) -> str:
    return s.rstrip(".!? ").strip()


def ensure_dir(path: str):
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


def safe_json_dump(path: str, data):
    ensure_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_external_terms() -> list[str]:
    """
    Lê ./english_terms.json no formato padrão.
    Se qualquer erro ocorrer, retorna lista vazia.
    """
    if not os.path.exists(EXTERNAL_TERMS_PATH):
        return []

    try:
        with open(EXTERNAL_TERMS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        terms = data.get("terms", [])
        if not isinstance(terms, list):
            return []

        return sorted({
            t.strip().lower()
            for t in terms
            if isinstance(t, str) and t.strip()
        })

    except Exception:
        return []


def get_next_groq_key() -> str:
    for _ in range(len(GROQ_KEYS)):
        key = next(_groq_key_cycle).get("key", "").strip()
        if key.startswith("gsk_"):
            return key
    raise RuntimeError("❌ Nenhuma GROQ API Key válida encontrada.")


def groq(prompt: str) -> str:
    last_error = None

    for _ in range(len(GROQ_KEYS)):
        api_key = get_next_groq_key()

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}]
        }

        try:
            res = requests.post(GROQ_URL, json=payload, headers=headers, timeout=20)

            if res.status_code == 429:
                last_error = "Rate limit"
                continue

            res.raise_for_status()
            raw = res.json()["choices"][0]["message"]["content"]
            return raw[raw.find("{"): raw.rfind("}") + 1]

        except requests.RequestException as e:
            last_error = str(e)
            continue

    raise RuntimeError(f"❌ Todas as GROQ keys falharam. Último erro: {last_error}")

# ================================================================================
# 1 — CORRIGIR + TRADUZIR (INALTERADO)
# ================================================================================

def correct_and_translate(text: str):
    prompt = f"""
You are an English teacher specializing in helping Brazilian students understand grammar, usage, and natural phrasing.
You are a private English teacher helping a software developer improve communication with a Dutch team that speaks English.

Your tasks:

1. Correct misspellings in Portuguese or English.
2. If the input is Portuguese → translate to natural English.
3. If partially Portuguese → translate entirely to English.
4. If the English has grammar mistakes → correct it.
5. ALWAYS output final English only.
6. When I put 'vs' between terms, I want to know the comparisons and meaning for each.
7. When the input contains the character "_" treat it as a missing word placeholder and apply CONTEXTUAL COMPLETION, replacing it with the most natural, semantically coherent term in English.

LEARNING-FOCUSED ENRICHMENT:
8. Internally identify relevant lexical chunks, collocations, and common expressions related to the corrected sentence.
9. Internally prefer natural spoken and professional English usage over literal translation.
10. Internally consider functional synonyms and alternative phrasings that a native speaker would naturally use in the same context.
11. Avoid unnatural word-by-word constructions influenced by Portuguese structure.

IMPORTANT:
Before producing the final JSON, apply the following internal reasoning standard even though it will NOT appear in the JSON output:

INTERNAL EXPLANATION PATTERN (do NOT output this explicitly):
- Identify what the student is really asking or trying to say.
- Fix the sentence in English.
- Infer and complete any missing terms represented by "_" using contextual meaning.
- Detect common Portuguese → English interference patterns.
- Identify natural chunks, collocations, and expressions.
- Select the most natural phrasing for professional communication.
- Understand WHY the mistake happens, especially comparing with Portuguese logic.
- Give a simple and natural pronunciation according to English usage.

- Apply grammar and usage rules:
   * when + present → future meaning  
   * correct order for questions
   * verb tenses and natural phrasing
- Internally generate:
   - corrected version
   - natural alternative phrasings
   - relevant chunks / expressions
   - functional synonyms
   - why it is correct
   - why the other form is wrong
   - examples of contrast

But do NOT output this explanation. Only use it to improve the correction.

Return ONLY JSON in the format:

{{
  "corrected": "final English",
  "had_error": true/false,
  "reason": "short explanation"
}}

Input: "{text}"
"""
    obj = json.loads(groq(prompt))
    obj["model_used"] = "Groq"
    return obj

# ================================================================================
# 2 — DEFINIÇÃO + EXEMPLOS (INALTERADO)
# ================================================================================

def generate_wordbank(term: str, external_terms: list[str]):
    example_specs = [
        {"level": lvl, "size": cfg["size"]}
        for lvl, cfg in LEVELS.items()
        if cfg["enabled"]
    ]

    examples_json = ",".join(
        f'{{"level":"{e["level"]}","size":"{e["size"]}","phrase":"..."}}'
        for e in example_specs
    )

    terms_block = ""
    if external_terms:
        terms_block = f"""
Use approximately 60% of the following terms across the examples.
Do NOT force all of them into a single sentence.
Use them naturally and spread them across different examples.
Available terms:
{", ".join(external_terms)}
"""

    prompt = f"""
Create the following JSON:

{{
 "definition_pt": "Tradução mais explicação natural e clara do significado em português, com dica gramatical simples.",
 "examples": [{examples_json}]
}}

Rules:
- Do NOT repeat the phrase at the beginning.
- Explain the meaning of "{term}" naturally in Portuguese.
- ALL examples must be FULL English sentences.
- ALL exemples, ALL phrase should make sense.
- Every example MUST contain the phrase "{term}".
- short → 4–8 words
- medium → 10–16 words
- long → 18–28 words
- Sound natural for each CEFR level.

{terms_block}
"""
    obj = json.loads(groq(prompt))
    obj["model_used"] = "Groq"
    return obj

# ================================================================================
# FILES / PREVIEW / PROCESSAMENTO / MAIN (INALTERADOS)
# ================================================================================

def save_create_later(item: str):
    item = sanitize_sentence(item)

    if not os.path.exists(CREATE_LATER):
        safe_json_dump(CREATE_LATER, {"pending": [item]})
        print(f"📌 CreateLater.json criado → {item}")
        return

    with open(CREATE_LATER, "r", encoding="utf-8") as f:
        data = json.load(f)

    if item not in data["pending"]:
        data["pending"].append(item)
        safe_json_dump(CREATE_LATER, data)
        print(f"📌 Adicionado → {item}")


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

    with open(FULL_RESULTS, "r", encoding="utf-8") as f:
        data = json.load(f)

    data.append(entry)
    safe_json_dump(FULL_RESULTS, data)
    print("📚 Registrado em TranscriptResults.json")

# ================================================================================  
# PREVIEW (INALTERADO)
# ================================================================================  

def print_preview(original, corrected, had_error, reason, definition_pt, examples, model):
    C_RESET = "\033[0m"
    C_RED = "\033[91m"
    C_GREEN = "\033[92m"
    C_BLUE = "\033[94m"
    C_YELLOW = "\033[93m"
    C_TITLE = "\033[96m\033[1m"

    print(f"{C_TITLE}\n══════════════════════════════════════")
    print("           PREVIEW DO TRANSCRIPT")
    print(f"══════════════════════════════════════{C_RESET}\n")

    print(f"Modelo usado: {model}\n")

    if had_error:
        print(f"{C_RED}Correção necessária:{C_RESET}")
        print(f"{C_YELLOW}Motivo: {reason}{C_RESET}")
        print(f"{C_GREEN}Corrigido: {corrected}{C_RESET}\n")
    else:
        print(f"{C_GREEN}Sem erros. Resultado: {corrected}{C_RESET}\n")

    print(f"{C_BLUE}Definição PT:{C_RESET} {definition_pt}\n")

    print(f"{C_BLUE}Exemplos:{C_RESET}")
    for ex in examples:
        print(f" ➜ ({ex['level']}, {ex['size']}) {ex['phrase']}")

# ================================================================================  
# PROCESSAMENTO
# ================================================================================  

def process_term(original: str):
    print("🔍 Processando:", original)

    result = correct_and_translate(original)
    corrected = sanitize_sentence(result["corrected"])

    save_create_later(corrected)

    external_terms = load_external_terms()
    wb = generate_wordbank(corrected, external_terms)

    print_preview(
        original,
        corrected,
        result["had_error"],
        result["reason"],
        wb["definition_pt"],
        wb["examples"],
        wb["model_used"]
    )

    save_transcript_result(corrected, wb["definition_pt"], wb["examples"])

def main():
    while True:
        if len(sys.argv) < 2:
            original = input("Digite a frase/termo a ser processado: ").strip()
            if not original:
                print("Nenhuma entrada fornecida. Encerrando.")
                return
        else:
            original = " ".join(sys.argv[1:]).strip()
            sys.argv = [sys.argv[0]]

        process_term(original)

        proximo = input(
            "\nDigite apenas 's' para sair\n"
            "OU digite a frase/termo a ser processado: "
        ).strip()

        if proximo.lower() == "s":
            gerar_pdf = input("\nDeseja gerar o PDF? (S/N): ").strip().lower()
            if gerar_pdf == "s":
                raw = "./last_groq_raw.txt"
                if os.path.exists(raw):
                    try:
                        os.remove(raw)
                    except Exception:
                        pass
                    
                print("📄 Gerando PDF via doc.py...")
                os.system("python ./doc.py")

            print("\nEncerrando o programa.")
            break
        else:
            sys.argv = [sys.argv[0], proximo]


if __name__ == "__main__":
    main()

