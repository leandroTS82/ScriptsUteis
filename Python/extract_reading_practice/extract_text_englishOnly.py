import json
import os
import re

# ==========================================================
# CONFIGURAÇÕES
# ==========================================================

INPUT_JSON_PATH = r"C:\dev\scripts\ScriptsUteis\Python\extract_reading_practice\extractedFromPdf\arquivo_deduplicado.json"
OUTPUT_JSON_PATH = r"C:\dev\scripts\ScriptsUteis\Python\extract_reading_practice\extractedFromPdf\saida_en_only.json"

# ==========================================================
# REGRA DE DETECÇÃO DE INÍCIO DO PORTUGUÊS
# (ajustada ao seu corpus)
# ==========================================================

PT_START = re.compile(
    r'^(Choveu|Durante|Quando|Apesar|Mesmo|Enquanto|Eu|Ela|Ele|Nós|Vocês|Foi|Fui|Era|Estava|Estão|Estavam)\b',
    re.IGNORECASE
)

# ==========================================================
# FUNÇÃO PRINCIPAL
# ==========================================================

def extract_english_only(text: str) -> str:
    """
    Extrai somente o trecho em inglês de um texto EN + PT.
    Assume que:
      - Inglês vem primeiro
      - Português começa em uma nova frase
    """
    if not text:
        return ""

    sentences = re.split(r'(?<=\.)\s+', text.strip())

    english_sentences = []

    for sentence in sentences:
        sentence = sentence.strip()

        # Detecta início claro de português
        if PT_START.match(sentence):
            break

        english_sentences.append(sentence)

    return " ".join(english_sentences).strip()

# ==========================================================
# PROCESSAMENTO DO JSON
# ==========================================================

def process_json(input_path: str, output_path: str):
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {input_path}")

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    stories = data.get("stories", [])
    if not isinstance(stories, list):
        raise ValueError("Formato inválido: 'stories' não é uma lista.")

    total = len(stories)
    cleaned = 0

    for story in stories:
        original_text = story.get("text", "")
        english_text = extract_english_only(original_text)

        if english_text != original_text:
            cleaned += 1

        story["text"] = english_text

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("Processamento concluído com sucesso.")
    print(f"Total de stories: {total}")
    print(f"Texts ajustados: {cleaned}")
    print(f"Arquivo gerado: {output_path}")

# ==========================================================
# EXECUÇÃO
# ==========================================================

if __name__ == "__main__":
    process_json(INPUT_JSON_PATH, OUTPUT_JSON_PATH)
