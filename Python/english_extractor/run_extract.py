import sys
from english_extractor import extract_and_enrich
from english_storage import save_enriched, generate_flat_terms


def run(text_en: str):
    enriched = extract_and_enrich(text_en)
    save_enriched(enriched)
    generate_flat_terms()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_extract.py \"English text here\"")
        sys.exit(1)

    run(sys.argv[1])
    print("✅ English content extracted and stored successfully")
