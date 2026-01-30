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
# CONFIGURAÇÕES INLINE
# ==========================================================
# ==========================================================
# GEMINI VOICES DISPONÍVEIS
# ==========================================================

GEMINI_VOICES = [
    "schedar",
    "charon",
    "kore",
    "puck",
    "fenrir"
]

def get_random_gemini_voice() -> str:
    """
    Retorna uma voice aleatória disponível para Gemini TTS
    """
    return random.choice(GEMINI_VOICES)

# GEMINI_VOICE = "schedar"
GEMINI_VOICE = get_random_gemini_voice()
print(f"🔊 Gemini voice selecionada: {GEMINI_VOICE}")

GEMINI_MAX_RETRIES = 3
GEMINI_RETRY_DELAY = 10  # segundos

# ==========================================================
# CONTROLE DE EXECUÇÃO / PRIORIDADE
# ==========================================================

# Delay entre um termo e outro (em segundos)
DELAY_BETWEEN_TERMS = 15   # ex: 15 = espera 15s entre cada termo

# Prioridade de execução:
# "high"    -> sem delay
# "normal"  -> usa DELAY_BETWEEN_TERMS
# "low"     -> delay dobrado
EXECUTION_PRIORITY = "low"   # high | normal | low


# ==========================================================
# PATHS (MANTIDOS + NOVO JSON DIR)
# ==========================================================

INPUT_JSON = Path(
    #r"C:\dev\scripts\ScriptsUteis\Python\AI_EnglishHelper\CreateLater2.json"
    r"C:\dev\scripts\ScriptsUteis\Python\AI_EnglishHelper\CreateLater\CreateLater_20260130.json"
)

AUDIO_OUTPUT_DIR = Path(
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - EnglishAudioLessons"
)

JSON_OUTPUT_DIR = Path(
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - EnglishAudioLessons\Json"
)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b"
TIMEOUT = 60

# ==========================================================
# PROMPTS (NOVO – PEDAGÓGICO)
# ==========================================================

PROMPTS = {
    "system": (
        "Your are a english Teacher. (dont say your name)"
        "You are a young, energetic, and modern English teacher for Brazilian students, "
        "with the style of a YouTuber and podcast host. "
        "You sound enthusiastic, friendly, motivating, and natural when speaking. "
        "Your teaching is optimized for AUDIO learning, memory retention, and real-life usage. "
        "You teach step by step, always helping intermediate (C1) students gain confidence. "
        "You strategically mix English with Portuguese to support learning without breaking flow. "
        "You explain things simply, clearly, and practically — never academically. "
        "You always sound like you are talking directly to the student. "
        "Return ONLY valid JSON. No extra text."
    ),

    "user": lambda term: f"""
Generate ONLY valid JSON.

You are teaching the English term "{term}" to a Brazilian student (level B1).
This content will be transformed into AUDIO (podcast / YouTube style),
so everything must sound NATURAL, SPOKEN, and ENGAGING.

General tone and style:
- Sound like a young YouTuber or podcast host.
- Be animated, positive, and modern.
- Speak directly to the student.
- Use short, clear sentences.
- Encourage confidence, repetition, and intuition.
- Focus on how people REALLY speak English.

Pedagogical rules:
- Start with a clear presentation (em português).
- Always help after English sentences with short explanations in Portuguese.
- Mix Portuguese explanations with English examples smoothly.
- Avoid long or academic explanations.
- Reinforce meaning through repetition and variation.

Return the following JSON structure exactly:

{{
  "term": "{term}",
  "tts_blocks": [
    "Start with an energetic and friendly presentation (em português), like a YouTuber, introducing the term '{term}' and why it is useful in real life.",
    
    "Give a short and clear SUMMARY in Portuguese explaining what the student will learn about '{term}'.",
    
    "Explain the meaning of '{term}' in simple (short, quickly), spoken English. After that, add a short help in Portuguese reinforcing the idea.",
    
    "Explain the same meaning again using different English words. Then briefly explain in Portuguese to reinforce understanding.",
    
    "Explique o significado de '{term}' em português, de forma prática, direta e sem complicação.",
    
    "Explain (short) how native speakers commonly use '{term}' in daily conversations, focusing on intention and natural tone. Add a short explanation in Portuguese.",
    
    "Explain when '{term}' is commonly used and when it should NOT be used, in Portuguese, with practical examples (short).",
    
    "Explain which verb tense or grammatical structure '{term}' usually appears with. Use English examples (short) and explain them briefly in Portuguese.",
    
    "Give two short and natural example (short) sentences using '{term}' in English. After each sentence, explain its meaning in Portuguese.",
    
    "Invite the student to repeat the sentences aloud. Motivate them like a coach or YouTuber, focusing on confidence and memory.",
    
    "Create a short and natural dialogue between two people using '{term}'. Keep the English simple and add a brief explanation in Portuguese after the dialogue.",
    
    "Give similar words or expressions to '{term}' in English. Briefly explain the differences in Portuguese.",
    
    "Give opposite or contrasting words or expressions to '{term}', with short explanations in Portuguese.",
    
    "Create a memorable association, analogy, or mental image to help the student never forget '{term}'. Explain it in Portuguese in a fun way.",
    
    "Summarize everything briefly in English, reinforcing the core meaning and usage of '{term}'. Then add a quick summary in Portuguese.",
    
    "Finish by asking the student a simple and friendly question in English using '{term}', encouraging them to answer out loud.",
    
    "Say goodbye in a fun, motivating YouTuber style, encouraging the student to keep practicing English."
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

def get_delay_by_priority() -> int:
    if EXECUTION_PRIORITY == "high":
        return 0
    if EXECUTION_PRIORITY == "low":
        return DELAY_BETWEEN_TERMS * 2
    return DELAY_BETWEEN_TERMS

def load_terms():
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        raw = json.load(f)

    normalized = []
    for item in raw.get("pending", []):
        if isinstance(item, str):
            normalized.append({
                "term": item,
                "status": "pending"
            })
        elif isinstance(item, dict):
            normalized.append(item)

    raw["pending"] = normalized
    return raw


def save_terms(data):
    with open(INPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


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
# GEMINI TTS COM RETRY
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
            raise RuntimeError("Áudio não gerado")

        except Exception:
            if attempt >= GEMINI_MAX_RETRIES:
                raise
            wait = GEMINI_RETRY_DELAY * attempt
            print(f"⏳ Retry Gemini ({attempt}) — aguardando {wait}s")
            time.sleep(wait)


# ==========================================================
# MAIN
# ==========================================================

def main():

    if len(sys.argv) > 1:
        print("🟦 Modo FRASE manual ativado\n")
        data = {
            "pending": [
                {
                    "term": " ".join(sys.argv[1:]).strip(),
                    "status": "pending"
                }
            ]
        }
    else:
        data = load_terms()

    terms = [t for t in data["pending"] if t.get("status") == "pending"]

    if not terms:
        print("ℹ Nenhum termo para processar.")
        return

    AUDIO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    JSON_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for idx, item in enumerate(terms, start=1):
        term = item["term"]
        print(f"[{idx}/{len(terms)}] 🔹 {term}")

        # ----------------------------
        # Marca como PROCESSING
        # ----------------------------
        item["status"] = "processing"
        save_terms(data)

        try:
            response = groq_request(PROMPTS["user"](term))
            raw = response["choices"][0]["message"]["content"]

            json_text = extract_json_block(raw)
            if not json_text:
                raise ValueError("JSON inválido do Groq")

            groq_payload = json.loads(json_text)

            safe_name = sanitize_filename(term)

            # ----------------------------
            # Salvar JSON estruturado (conteúdo Groq)
            # ----------------------------
            json_path = JSON_OUTPUT_DIR / f"{safe_name}.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(groq_payload, f, ensure_ascii=False, indent=2)

            # ----------------------------
            # TTS
            # ----------------------------
            tts_lines = []
            for block in groq_payload["tts_blocks"]:
                tts_lines.append(block)
                tts_lines.append('<break time="0.6s"/>')

            final_tts = "\n".join(tts_lines)

            audio_path = AUDIO_OUTPUT_DIR / f"{safe_name}.wav"
            generate_audio_safe(final_tts, audio_path)

            # ----------------------------
            # Marca como DONE
            # ----------------------------
            item["status"] = "done"

        except Exception as e:
            # ----------------------------
            # Marca como ERROR
            # ----------------------------
            item["status"] = "error"
            print(f"⛔ Erro ao processar '{term}': {e}")
            print("➡ Termo ignorado, batch continua.\n")

        finally:
            # ----------------------------
            # Persistência garantida
            # ----------------------------
            save_terms(data)

        # ----------------------------
        # DELAY ENTRE TERMOS
        # ----------------------------
        delay = get_delay_by_priority()
        if delay > 0 and idx < len(terms):
            print(f"⏸️ Aguardando {delay}s antes do próximo termo...")
            time.sleep(delay)


        print("\n✅ Processo finalizado")
        print("🎧 Áudios:", AUDIO_OUTPUT_DIR)
        print("📄 JSONs :", JSON_OUTPUT_DIR)


if __name__ == "__main__":
    main()
