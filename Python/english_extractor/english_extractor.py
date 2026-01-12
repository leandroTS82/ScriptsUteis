import json
from groq_client import groq_chat


def extract_and_enrich(text_en: str) -> dict:
    """
    Recebe texto em inglês e retorna JSON enriquecido:
    terms, chunks, expressions, discourse_markers
    """

    prompt = f"""
From the English text below, extract and enrich:

1. terms (important vocabulary)
2. chunks (collocations or lexical chunks)
3. expressions (idiomatic or fixed expressions)
4. discourse_markers (functional equivalence such as anyway, however, in fact)

Rules:
- No duplicates
- English text as 'text'
- Include Portuguese meaning
- Include short usage explanation
- Include one natural English example
- Output ONLY valid JSON

Expected JSON format:
{{
  "terms": [],
  "chunks": [],
  "expressions": [],
  "discourse_markers": []
}}

Text:
{text_en}
"""

    raw = groq_chat(prompt)
    return json.loads(raw)
