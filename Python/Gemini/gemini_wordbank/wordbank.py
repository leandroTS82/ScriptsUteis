"""
====================================================================================
 Script: wordbank.py (versão final minimalista para Gemini)
 Funções:
   - Detectar idioma e traduzir PT → EN corrigindo ortografia
   - Corrigir frases em inglês com erro (grammar fix)
   - Exibir preview amigável e colorido mostrando:
       ✔ aviso de frase incorreta
       ✔ palavra/frase corrigida
       ✔ definição PT
       ✔ 3 exemplos EN com nível (A2, B1, B2)
   - Registrar a palavra corrigida no CreateLater.json
   - Usar o modelo MAIS BARATO: gemini-2.0-flash
====================================================================================
"""

import os
import sys
import json
import google.generativeai as genai

# ================================================================================
# CONFIG
# ================================================================================
KEY_PATH = r"C:\dev\scripts\ScriptsUteis\Python\Gemini\google-gemini-key.txt"
OUTPUT_DIR = r"C:\dev\scripts\ScriptsUteis\Python\ContentFabric\1GroqIA_WordBank\2ContentToCreate"
MODEL = "gemini-2.0-flash"

api_key = open(KEY_PATH, "r", encoding="utf-8").read().strip()
genai.configure(api_key=api_key)


# ================================================================================
# 1. Traduzir PT → EN OU corrigir inglês misturado
# ================================================================================
def translate_or_fix_sentence(text):
    """
    - Se for PT → traduz para EN
    - Se for inglês errado → corrige
    - Se estiver misturado → corrige e traduz a parte necessária
    - Retorna a frase corrigida em inglês E indica se havia erro
    """
    prompt = f"""
    You will receive a sentence that may contain:
    - Portuguese words,
    - incorrect English grammar,
    - or both mixed.

    Tasks:
    1. Detect if the sentence is correct English.
    2. If it contains Portuguese → translate to English.
    3. If the English is incorrect → fix grammar completely.
    4. Return ONLY a JSON object with:
       {{
         "corrected": "the corrected English sentence",
         "had_error": true or false
       }}

    Input sentence: "{text}"
    """

    model = genai.GenerativeModel(MODEL)
    resp = model.generate_content(prompt)

    try:
        data = json.loads(resp.text)
    except:
        start = resp.text.find("{")
        end = resp.text.rfind("}") + 1
        data = json.loads(resp.text[start:end])

    return data["corrected"], data["had_error"]


# ================================================================================
# 2. Gerar conteúdo estilo WordBank (preview)
# ================================================================================
def generate_preview_content(corrected_sentence):
    prompt = f"""
    Create a WordBank-style JSON explanation for the English phrase:
    "{corrected_sentence}"

    You MUST return ONLY this JSON structure:
    {{
      "definition_pt": "explicação NATURAL em português explicando o significado",
      "examples": [
        {{
          "level": "A2",
          "phrase": "Example sentence #1 in English using the phrase"
        }},
        {{
          "level": "B1",
          "phrase": "Example sentence #2 in English using the phrase"
        }},
        {{
          "level": "B2",
          "phrase": "Example sentence #3 in English using the phrase"
        }}
      ]
    }}

    RULES:
    - ALL example sentences MUST be in ENGLISH.
    - ALL examples MUST use the corrected phrase exactly: {corrected_sentence}
    - The Portuguese definition MUST NOT include extra explanations beyond meaning.
    - No Portuguese words allowed in example sentences.
    - Only return valid JSON. No markdown, no comments.
    """

    model = genai.GenerativeModel(MODEL)
    resp = model.generate_content(prompt)

    try:
        data = json.loads(resp.text)
    except:
        start = resp.text.find("{")
        end = resp.text.rfind("}") + 1
        data = json.loads(resp.text[start:end])

    return data


# ================================================================================
# 3. Preview colorido
# ================================================================================
def print_preview(original, corrected, had_error, definition_pt, examples):
    C_RESET = "\033[0m"
    C_RED = "\033[91m"
    C_GREEN = "\033[92m"
    C_BLUE = "\033[94m"
    C_YELLOW = "\033[93m"
    C_TITLE = "\033[96m\033[1m"

    print(f"\n{C_TITLE}══════════════════════════════════════════════════")
    print(f"                 PREVIEW DO WORDBANK")
    print(f"══════════════════════════════════════════════════{C_RESET}\n")

    if had_error:
        print(f"{C_RED}A frase “{original}” está incorreta.{C_RESET}")
        print(f"{C_GREEN}Forma correta: {corrected}{C_RESET}\n")
    else:
        print(f"{C_GREEN}A frase está correta!{C_RESET}\n")

    print(f"{C_BLUE}Palavra-chave: {corrected}{C_RESET}")
    print(f"{C_YELLOW}📘 Definição PT: {definition_pt}{C_RESET}\n")

    print(f"{C_BLUE}Exemplos:{C_RESET}")
    for ex in examples:
        print(f"   ➜ ({ex['level']}) {ex['phrase']}")

    print("\n")


# ================================================================================
# 4. Atualizar CreateLater.json
# ================================================================================
def update_create_later(word):
    path = OUTPUT_DIR +"./CreateLater.json"

    if not os.path.exists(path):
        data = {"pending": [word]}
        open(path, "w", encoding="utf-8").write(json.dumps(data, indent=2))
        print(f"📌 CreateLater.json criado e palavra adicionada: {word}")
        return

    data = json.load(open(path, "r", encoding="utf-8"))

    if word not in data["pending"]:
        data["pending"].append(word)
        open(path, "w", encoding="utf-8").write(json.dumps(data, indent=2))
        print(f"📌 Palavra adicionada: {word}")


# ================================================================================
# MAIN
# ================================================================================
def main():
    if len(sys.argv) < 2:
        print("Uso: python wordbank.py \"frase aqui\"")
        return

    original_sentence = " ".join(sys.argv[1:]).strip()

    print("🔍 Processando:", original_sentence)

    # 1) Corrigir e/ou traduzir sentença
    corrected_sentence, had_error = translate_or_fix_sentence(original_sentence)

    # 2) Registrar no CreateLater.json
    update_create_later(corrected_sentence)

    # 3) Gerar conteúdo para preview
    content = generate_preview_content(corrected_sentence)

    # 4) Renderizar preview
    print_preview(
        original_sentence,
        corrected_sentence,
        had_error,
        content["definition_pt"],
        content["examples"]
    )


if __name__ == "__main__":
    main()
