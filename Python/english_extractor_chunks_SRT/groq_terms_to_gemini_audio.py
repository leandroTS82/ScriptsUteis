"""
============================================================
 Script: groq_terms_to_gemini_audio.py
 Autor: Leandro
============================================================
"""

import os
import sys
import json
import random
import requests
import unicodedata
import re
from itertools import cycle
from pathlib import Path

# ==========================================================
# PATHS (MANTIDOS)
# ==========================================================

INPUT_JSON = Path(
    r"C:\dev\scripts\ScriptsUteis\Python\english_extractor_chunks_SRT\terms\pending_terms.json"
)

OUTPUT_JSON = Path(
    r"C:\dev\scripts\ScriptsUteis\Python\english_extractor_chunks_SRT\terms\terms_audio_payload.json"
)

AUDIO_OUTPUT_DIR = Path(
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\NewAudios_Gemini"
)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b"
TIMEOUT = 60

# ==========================================================
# IMPORTS DO ECOSSISTEMA
# ==========================================================

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from groq_keys_loader import GROQ_KEYS

MAKE_VIDEO_GEMINI_DIR = r"C:\dev\scripts\ScriptsUteis\Python\Gemini\MakeVideoGemini"
if MAKE_VIDEO_GEMINI_DIR not in sys.path:
    sys.path.insert(0, MAKE_VIDEO_GEMINI_DIR)

from generate_audio import generate_audio

# ==========================================================
# VALIDAÇÕES
# ==========================================================

if not GROQ_KEYS:
    raise RuntimeError("❌ GROQ_KEYS não carregadas")

_groq_key_cycle = cycle(random.sample(GROQ_KEYS, len(GROQ_KEYS)))

# ==========================================================
# HELPERS
# ==========================================================

def sanitize_filename(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode()
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s_-]", "", text)
    return re.sub(r"\s+", "_", text).strip("_")


def extract_json_block(text: str) -> str | None:
    """
    Extrai o primeiro bloco JSON válido do texto.
    """
    match = re.search(r"\{[\s\S]*\}", text)
    return match.group(0) if match else None


# ==========================================================
# GROQ
# ==========================================================

def groq_request(prompt: str) -> dict:
    api_key = next(_groq_key_cycle)["key"]

    r = requests.post(
        GROQ_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": GROQ_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an young English teacher focused on memory retention. "
                        "Return ONLY valid JSON."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.4
        },
        timeout=TIMEOUT
    )

    r.raise_for_status()
    return r.json()


def build_prompt(term: str) -> str:
    return f"""
Generate ONLY valid JSON:

{{
  "term": "{term}",
  "tts_blocks": [
    "Explain the meaning of '{term}' in English, clearly and simply.",
    "Repeat the explanation of '{term}' in English using different words.",
    "Explique o significado de '{term}' em português.",
    "Give a memorable native and comum usage tip so this term is never forgotten.",
    "Me de uma alusão do uso comum nativo para que este termo nunca seja esquecido.",
    "Short example sentence using '{term}'.",
    "Another short example sentence using '{term}'.",
    "Use '{term}' in a short dialog between two people.",
    "give the similar words or phrases to '{term}' in English.",
    "give the opposite words or phrases to '{term}' in English.",
    "Provide a brief summary of everything above in English."
    "finish with a question to the student to test their understanding of '{term}'."
  ]
}}
"""


# ==========================================================
# MAIN
# ==========================================================

def main():

    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        terms = json.load(f).get("pending", [])

    AUDIO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)

    results = []

    for idx, term in enumerate(terms, start=1):
        print(f"[{idx}/{len(terms)}] 🔹 {term}")

        try:
            response = groq_request(build_prompt(term))
            raw = response["choices"][0]["message"]["content"]

            json_text = extract_json_block(raw)
            if not json_text:
                raise ValueError("JSON não encontrado na resposta do Groq")

            data = json.loads(json_text)

            # ----------------------------
            # TTS
            # ----------------------------
            tts_lines = []
            for t in data["tts_blocks"]:
                tts_lines.append(t)
                tts_lines.append('<break time="0.6s"/>')

            final_tts = "\n".join(tts_lines)

            safe_name = sanitize_filename(term)
            audio_path = AUDIO_OUTPUT_DIR / f"{safe_name}.wav"

            # ----------------------------
            # GEMINI (VALIDADO)
            # ----------------------------
            generate_audio(
                text=final_tts,
                output_path=str(audio_path),
                voice="schedar"
            )

            if not audio_path.exists():
                raise RuntimeError("Gemini não gerou áudio")

            data["audio_file"] = str(audio_path)
            results.append(data)

        except Exception as e:
            print(f"⛔ Erro ao processar '{term}': {e}")
            print("➡ Termo ignorado, batch continua.\n")

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("\n✅ Processo finalizado")
    print("🎧 Áudios:", AUDIO_OUTPUT_DIR)
    print("📄 JSON:", OUTPUT_JSON)


if __name__ == "__main__":
    main()
