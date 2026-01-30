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
import time
from itertools import cycle
from pathlib import Path

# ==========================================================
# CONFIGURAÇÕES INLINE (NOVAS)
# ==========================================================

GEMINI_VOICE = "schedar"   # <<< MUDE A VOZ AQUI
GEMINI_MAX_RETRIES = 3
GEMINI_RETRY_DELAY = 4    # segundos (base, com backoff)

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
# PROMPTS (CENTRALIZADOS – CONTEÚDO INTACTO)
# ==========================================================

PROMPTS = {
    "system": (
        "You are a friendly and dynamic English teacher for Brazilian students. "
        "You speak in a natural, conversational tone, optimized for audio learning and memory retention. "
        "You always teach step by step, mixing English and Portuguese strategically. "
        "Return ONLY valid JSON. No extra text."
    ),

    "user": lambda term: f"""
Generate ONLY valid JSON.
Your name is Teacher Leandrinho.
You are a young teacher like a youtuber and you are teaching the English term "{term}" to a Brazilian student.
This content will be transformed into AUDIO, so write everything as if you were SPEAKING naturally.

Pedagogical rules:
- Be clear, friendly, and motivating.
- Mix Portuguese explanations with English examples.
- Use short sentences suitable for listening.
- Encourage repetition and active participation.
- Focus on memory, real usage, and intuition.
- Avoid long academic explanations.

Return the following JSON structure exactly:

{{
  "term": "{term}",
  "tts_blocks": [

    "Start with a short and engaging introduction in Portuguese explaining why the term '{term}' is useful in real life.",

    "Explain the meaning of '{term}' in simple English, as if speaking to a beginner.",

    "Explain the same meaning again in different English words, reinforcing understanding.",

    "Explique o significado de '{term}' em português, de forma clara, prática e didática.",

    "Explain how natives commonly use '{term}' in daily conversations, including tone and intention.",

    "Explain when '{term}' is commonly used and when it should NOT be used, in Portuguese.",

    "Explain which verb tense or grammatical structure '{term}' usually appears with, using Portuguese explanations and English examples.",

    "Give two short example sentences using '{term}'. Pause mentally between them to allow repetition.",

    "Invite the student to repeat the sentences aloud using '{term}', encouraging memory retention.",

    "Create a short and natural dialogue between two people using '{term}', with simple English.",

    "Give similar words or expressions to '{term}' in English, explaining small differences briefly in Portuguese.",

    "Give opposite or contrasting words or expressions to '{term}', with short explanations.",

    "Provide a memorable association, analogy, or mental image to help the student never forget '{term}'.",

    "Summarize everything briefly in English, reinforcing the core meaning and usage of '{term}'.",

    "Finish by asking the student a simple question in English using '{term}' to test understanding."
  ]
}}
"""
}

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
                {"role": "system", "content": PROMPTS["system"]},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.4
        },
        timeout=TIMEOUT
    )

    r.raise_for_status()
    return r.json()


# ==========================================================
# GEMINI TTS COM RETRY / RATE LIMIT
# ==========================================================

def generate_audio_safe(text: str, output_path: Path):
    for attempt in range(1, GEMINI_MAX_RETRIES + 1):
        try:
            generate_audio(
                text=text,
                output_path=str(output_path),
                voice=GEMINI_VOICE
            )

            if output_path.exists():
                return

            raise RuntimeError("Arquivo de áudio não gerado")

        except Exception as e:
            if attempt >= GEMINI_MAX_RETRIES:
                raise

            wait = GEMINI_RETRY_DELAY * attempt
            print(f"⏳ Gemini falhou (tentativa {attempt}). Aguardando {wait}s...")
            time.sleep(wait)


# ==========================================================
# MAIN
# ==========================================================

def main():

    # ------------------------------------------------------
    # MODO FRASE VIA ARGUMENTO
    # ------------------------------------------------------
    if len(sys.argv) > 1:
        terms = [" ".join(sys.argv[1:]).strip()]
        print("🟦 Modo FRASE manual ativado\n")
    else:
        with open(INPUT_JSON, "r", encoding="utf-8") as f:
            terms = json.load(f).get("pending", [])

    if not terms:
        print("ℹ Nenhum termo para processar.")
        return

    AUDIO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)

    results = []

    for idx, term in enumerate(terms, start=1):
        print(f"[{idx}/{len(terms)}] 🔹 {term}")

        try:
            response = groq_request(PROMPTS["user"](term))
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

            generate_audio_safe(final_tts, audio_path)

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
