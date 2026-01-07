import json
import os

# ==========================================================
# CONFIGURAÇÕES
# ==========================================================

INPUT_JSON_PATH = r"C:\dev\scripts\ScriptsUteis\Python\extract_reading_practice\extractedFromPdf\reading_practice_stories.json"
OUTPUT_JSON_PATH = r"C:\dev\scripts\ScriptsUteis\Python\extract_reading_practice\extractedFromPdf\arquivo_deduplicado.json"

# ==========================================================
# PROCESSAMENTO
# ==========================================================

def deduplicate_stories_by_text(input_path: str, output_path: str):
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {input_path}")

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    stories = data.get("stories", [])
    if not isinstance(stories, list):
        raise ValueError("Formato inválido: 'stories' não é uma lista.")

    unique_by_text = {}

    for story in stories:
        text = story.get("text", "").strip()
        title = story.get("title", "").strip()

        if not text:
            continue

        if text not in unique_by_text:
            unique_by_text[text] = story
        else:
            existing_title = unique_by_text[text].get("title", "")
            if len(title) < len(existing_title):
                unique_by_text[text] = story

    cleaned_stories = list(unique_by_text.values())

    output_data = {
        **data,
        "stories": cleaned_stories
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print("Deduplicação concluída com sucesso.")
    print(f"Total original: {len(stories)}")
    print(f"Total após limpeza: {len(cleaned_stories)}")
    print(f"Arquivo salvo em: {output_path}")

# ==========================================================
# EXECUÇÃO
# ==========================================================

if __name__ == "__main__":
    deduplicate_stories_by_text(INPUT_JSON_PATH, OUTPUT_JSON_PATH)
