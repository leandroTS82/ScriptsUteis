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

# ================================================================================
# CONFIG - CHAVE DIRETA
# ================================================================================

GROQ_API_KEY = "***"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b"

CREATE_LATER = "./CreateLater.json"
FULL_RESULTS = "./TranscriptResults.json"

# LEVELS embutidos
LEVELS = {
    "A1": {"enabled": True,  "size": "short"},
    "A2": {"enabled": True,  "size": "medium"},
    "B1": {"enabled": True,  "size": "medium"},
    "B2": {"enabled": False, "size": "long"},
    "C1": {"enabled": False, "size": "long"},
    "C2": {"enabled": False, "size": "long"}
}


# ================================================================================
# HELPERS
# ================================================================================

def sanitize_sentence(s):
    return s.rstrip(".!? ").strip()


def safe_json_dump(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def groq(prompt):
    """Função única e otimizada para chamadas Groq."""
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": GROQ_MODEL, "messages": [{"role": "user", "content": prompt}]}

    res = requests.post(GROQ_URL, json=payload, headers=headers, timeout=20)
    res.raise_for_status()

    raw = res.json()["choices"][0]["message"]["content"]
    return raw[raw.find("{"): raw.rfind("}") + 1]


# ================================================================================
# 1 — CORRIGIR + TRADUZIR (GROQ)
# ================================================================================

def correct_and_translate(text):

    prompt = f"""
                Your tasks:

                1. Correct misspellings in Portuguese or English.
                2. If the input is Portuguese → translate to natural English.
                3. If partially Portuguese → translate to English.
                4. If English has grammar mistakes → correct it.
                5. ALWAYS output final English only.

                Return ONLY JSON:
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
# 2 — DEFINIÇÃO + EXEMPLOS (GROQ)
# ================================================================================

def generate_wordbank(term):

    example_specs = [
        {"level": lvl, "size": cfg["size"]}
        for lvl, cfg in LEVELS.items()
        if cfg["enabled"]
    ]

    examples_json = ",".join(
        [f'{{"level":"{e["level"]}","size":"{e["size"]}","phrase":"..."}}' for e in example_specs]
    )

    prompt = f"""
Create the following JSON:

{{
 "definition_pt": "Tradução mais explicação natural e clara do significado em português, dicas gramaticais, de 1 exemplo simples de como seria em portugUês.",
 "examples": [{examples_json}]
}}

Rules:
- Do NOT repeat the phrase at the beginning.
- Explain the meaning of "{term}" in Portuguese naturally.
- ALL sentences must be FULL English sentences.
- Every example MUST contain the phrase "{term}".
- short → 4–8 words
- medium → 10–16 words
- long → 18–28 words
- NO isolated phrase alone.
- Must sound natural for each CEFR level.

Return ONLY JSON.
"""

    obj = json.loads(groq(prompt))
    obj["model_used"] = "Groq"
    return obj


# ================================================================================
# ARQUIVOS
# ================================================================================

def save_create_later(item):
    item = sanitize_sentence(item)

    if not os.path.exists(CREATE_LATER):
        safe_json_dump(CREATE_LATER, {"pending": [item]})
        print(f"📌 CreateLater.json criado → {item}")
        return

    data = json.load(open(CREATE_LATER, "r", encoding="utf-8"))
    if item not in data["pending"]:
        data["pending"].append(item)
        safe_json_dump(CREATE_LATER, data)
        print(f"📌 Adicionado → {item}")


def save_transcript_result(palavra, definicao, exemplos):
    entry = {"palavra_chave": palavra, "definicao_pt": definicao, "exemplos": exemplos}

    if not os.path.exists(FULL_RESULTS):
        safe_json_dump(FULL_RESULTS, [entry])
        print("📚 TranscriptResults.json criado!")
        return

    data = json.load(open(FULL_RESULTS, "r", encoding="utf-8"))
    data.append(entry)
    safe_json_dump(FULL_RESULTS, data)
    print("📚 Registrado em TranscriptResults.json")


# ================================================================================
# PREVIEW
# ================================================================================

def print_preview(original, corrected, had_error, reason, definition_pt, examples, model):

    C_RESET = "\033[0m"
    C_RED = "\033[91m"
    C_GREEN = "\033[92m"
    C_BLUE = "\033[94m"
    C_YELLOW = "\033[93m"
    C_TITLE = "\033[96m\033[1m"

    print(f"{C_TITLE}\n══════════════════════════════════════")
    print(f"           PREVIEW DO TRANSCRIPT")
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
# LÓGICA PRINCIPAL EXTRAÍDA PARA REUTILIZAÇÃO
# ================================================================================

def process_term(original):
    print("🔍 Processando:", original)

    # 1. Correção e tradução
    result = correct_and_translate(original)
    corrected = sanitize_sentence(result["corrected"])

    # 2. Registrar CreateLater
    save_create_later(corrected)

    # 3. Definição e exemplos
    wb = generate_wordbank(corrected)

    # 4. Preview
    print_preview(
        original,
        corrected,
        result["had_error"],
        result["reason"],
        wb["definition_pt"],
        wb["examples"],
        wb["model_used"]
    )

    # 5. Salvar resultado final
    save_transcript_result(corrected, wb["definition_pt"], wb["examples"])



# ================================================================================
# MAIN COM LOOP E PDF
# ================================================================================

def main():

    while True:

        # Solicitar input caso nenhum argumento tenha sido passado
        if len(sys.argv) < 2:
            print("Nenhum termo informado.")
            original = input("Digite a frase/termo a ser processado: ").strip()

            if not original:
                print("Nenhuma entrada fornecida. Encerrando.")
                return
        else:
            original = " ".join(sys.argv[1:]).strip()
            sys.argv = [sys.argv[0]]  # limpar argumentos após o primeiro ciclo

        # Executar processamento
        process_term(original)

        # PDF opcional
        gerar_pdf = input("\nDeseja gerar o PDF? (S/N): ").strip().lower()
        if gerar_pdf == "s":
            print("📄 Gerando PDF via doc.py...")
            os.system("python ./doc.py")

        # Novo termo?
        repetir = input("\nDeseja buscar um novo termo? (S/N): ").strip().lower()
        if repetir != "s":
            print("\nEncerrando o programa.")
            break



if __name__ == "__main__":
    main()
