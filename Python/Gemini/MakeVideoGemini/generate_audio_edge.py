# ============================================================
# generate_audio_edge.py
# Geração de áudio via Microsoft Edge TTS (edge-tts).
# ============================================================

import os
import asyncio
import io
import re
from pydub import AudioSegment

try:
    import edge_tts
except ImportError:
    raise ImportError(
        "[generate_audio_edge] Instale a dependência: pip install edge-tts"
    )


# ------------------------------------------------------------------
# CONFIGURAÇÃO DE VOZES
# ------------------------------------------------------------------

VOICE_CONFIG = {
    "en": "en-US-BrianMultilingualNeural",
    "pt": "en-US-BrianMultilingualNeural",
}

BILINGUAL_MODE = True

# Controle de emoção
USE_EMOTIONAL_PT_TEXT = True


# ------------------------------------------------------------------
# VELOCIDADE E TOM
# ------------------------------------------------------------------

RATE_CONFIG = {
    "en": "-25%",
    "pt": "+0%",  # corrigido
}

PITCH_CONFIG = {
    "en": "+3Hz",
    "pt": "+0Hz",
}


# ------------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------------

def _get_voice(lang: str) -> str:
    effective = lang if BILINGUAL_MODE else "en"
    return VOICE_CONFIG.get(effective, VOICE_CONFIG["en"])


def _get_rate(lang: str) -> str:
    effective = lang if BILINGUAL_MODE else "en"
    return RATE_CONFIG.get(effective, RATE_CONFIG["en"])


def _get_pitch(lang: str) -> str:
    effective = lang if BILINGUAL_MODE else "en"
    return PITCH_CONFIG.get(effective, PITCH_CONFIG["en"])


def _clean_text(text: str) -> str:
    text = text.replace("—", ",").replace("–", ",")
    text = "".join(c for c in text if c.isprintable())

    # NÃO remover ! e ?
    text = text.strip(" ,;:-")

    if text and text[-1] not in ".!?,":
        text += "."
    return text.strip()


# ------------------------------------------------------------------
# TTS
# ------------------------------------------------------------------

async def _synthesize_async(text: str, voice: str, rate: str, pitch: str) -> bytes:
    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=rate,
        pitch=pitch,
    )

    buf = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buf.write(chunk["data"])

    buf.seek(0)
    data = buf.read()

    if not data:
        raise edge_tts.exceptions.NoAudioReceived(
            f"Nenhum áudio recebido: '{text[:60]}'"
        )

    return data


def _synthesize_segment(
    text: str,
    lang: str,
    rate_override: str | None = None,
    pitch_override: str | None = None
) -> AudioSegment | None:

    voice = _get_voice(lang)
    rate  = rate_override or _get_rate(lang)
    pitch = pitch_override or _get_pitch(lang)
    text  = _clean_text(text)

    if not text:
        return None

    for attempt, (r, p) in enumerate([
        (rate, pitch),
        (rate, "+0Hz"),   # mantém emoção no retry
        ("+0%", "+0Hz"),
    ], start=1):
        try:
            mp3_bytes = asyncio.run(_synthesize_async(text, voice, r, p))
            return AudioSegment.from_file(io.BytesIO(mp3_bytes), format="mp3")

        except Exception as e:
            print(f"⚠️ tentativa {attempt} falhou ({e})")

    return None


def _pause_segment(ms: int) -> AudioSegment:
    return AudioSegment.silent(duration=ms)


# ------------------------------------------------------------------
# EMOÇÃO
# ------------------------------------------------------------------

def _split_emotional_pt_text(text: str) -> list[dict]:
    text = _clean_text(text)

    parts = re.split(r"([.!?])", text)
    result = []

    for i in range(0, len(parts), 2):
        sentence = parts[i].strip()
        punctuation = parts[i + 1] if i + 1 < len(parts) else "."

        if not sentence:
            continue

        final_text = f"{sentence}{punctuation}"

        pause = 120
        rate = "+5%"
        pitch = "+0Hz"

        if punctuation == "!":
            pause = 180
            rate = "+12%"
            pitch = "+6Hz"

        elif punctuation == "?":
            pause = 220
            rate = "+3%"
            pitch = "+5Hz"

        # regex melhorado
        lower = sentence.lower()
        if re.search(r"\b(bora|vamos|arrasando|excelente|muito bem|continue|praticando|galera)\b", lower):
            rate = "+12%"
            pitch = "+7Hz"
            pause = max(pause, 200)

        result.append({
            "text": final_text,
            "pause_ms": pause,
            "rate": rate,
            "pitch": pitch
        })

    return result


# ------------------------------------------------------------------
# SEGMENTOS
# ------------------------------------------------------------------

def _build_segments(lesson_json: dict) -> list:
    repeat_en = lesson_json["repeat_each"]["en"]
    repeat_pt = lesson_json["repeat_each"]["pt"]

    segments = []

    intro = lesson_json.get("introducao", "").strip()
    intro_lang = lesson_json.get("intro_lang", "pt")

    if intro:
        if USE_EMOTIONAL_PT_TEXT and intro_lang == "pt":
            for part in _split_emotional_pt_text(intro):
                segments.append({
                    "text": part["text"],
                    "lang": "pt",
                    "pause_ms": part["pause_ms"],
                    "rate": part["rate"],
                    "pitch": part["pitch"]
                })
        else:
            segments.append({
                "text": intro,
                "lang": intro_lang,
                "pause_ms": 700
            })

        segments.append({"text": "", "lang": intro_lang, "pause_ms": 700})

    for group in lesson_json["WORD_BANK"]:
        for index, item in enumerate(group):
            text = item["text"].strip()
            lang = item.get("lang", "en")
            pause_ms = item.get("pause", 1000)
            repeat = repeat_en if lang == "en" else repeat_pt

            is_final_pt = lang == "pt" and index == len(group) - 1

            if is_final_pt:
                if USE_EMOTIONAL_PT_TEXT:
                    for part in _split_emotional_pt_text(text):
                        segments.append({
                            "text": part["text"],
                            "lang": "pt",
                            "pause_ms": part["pause_ms"],
                            "rate": part["rate"],
                            "pitch": part["pitch"]
                        })
                else:
                    segments.append({
                        "text": text,
                        "lang": "pt",
                        "pause_ms": pause_ms
                    })

                segments.append({"text": "", "lang": "pt", "pause_ms": pause_ms})
                continue

            for _ in range(repeat):
                segments.append({
                    "text": text,
                    "lang": lang,
                    "pause_ms": 0
                })

            segments.append({"text": "", "lang": lang, "pause_ms": pause_ms})

    return segments


# ------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------

def generate_audio_edge(lesson_json: dict, output_path: str) -> str:
    print("🎤 Edge TTS")

    segments = _build_segments(lesson_json)
    combined = AudioSegment.silent(duration=300)

    for seg in segments:
        text = seg["text"]
        lang = seg["lang"]
        pause = seg["pause_ms"]

        if text:
            audio = _synthesize_segment(
                text,
                lang,
                rate_override=seg.get("rate"),
                pitch_override=seg.get("pitch")
            )

            if audio:
                combined += audio
            else:
                combined += _pause_segment(800)

        if pause:
            combined += _pause_segment(pause)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    combined.export(output_path, format="wav")

    print("✔ áudio gerado")
    return output_path


# ------------------------------------------------------------------
# TESTE
# ------------------------------------------------------------------

if __name__ == "__main__":
    lesson = {
        "repeat_each": {"pt": 1, "en": 2},
        "introducao": "Fala pessoal! Hoje vamos aprender uma palavra nova!",
        "intro_lang": "pt",
        "WORD_BANK": [
            [
                {"lang": "en", "text": "resilient"},
                {"lang": "pt", "text": "Resiliente, que se recupera facilmente."},
                {"lang": "en", "text": "She is very resilient after hard times."},
                {"lang": "pt", "text": "Muito bem! Continue praticando! Voce esta arrasando!"}
            ]
        ]
    }

    generate_audio_edge(lesson, "outputs/audio/test.wav")