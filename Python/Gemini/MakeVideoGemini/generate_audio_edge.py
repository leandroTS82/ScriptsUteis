
# ============================================================
# generate_audio_edge.py
#
# Edge TTS Multilingual AI Voice Engine
#
# Objetivo:
# - PT pronunciado como PT
# - EN pronunciado como EN
# - mesma voz Brian
# - creator style
# - listening practice
# - emotional rendering
# - AI-directed pacing
#
# ============================================================

import os
import io
import sys
import asyncio

from pydub import AudioSegment

try:
    import edge_tts

except ImportError:
    raise ImportError(
        "Instale: pip install edge-tts"
    )


# ============================================================
# IMPORT ENRICHER
# ============================================================

CURRENT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from multilingual_tts_enricher_groq import (
    enrich_text
)


# ============================================================
# CONFIG
# ============================================================

VOICE_EN = "en-US-BrianMultilingualNeural"

VOICE_PT = "pt-BR-AntonioNeural"


# ============================================================
# HELPERS
# ============================================================

def _clean_text(text: str) -> str:

    text = text.replace("—", ",")

    text = text.replace("–", ",")

    text = "".join(
        c for c in text
        if c.isprintable()
    )

    text = text.strip()

    if text and text[-1] not in ".!?":
        text += "."

    return text


def _pause(ms: int):

    return AudioSegment.silent(
        duration=ms
    )


# ============================================================
# VOICE PARAMS
# ============================================================

def _resolve_voice_params(
    lang: str,
    energy: str,
    style: str
):

    # --------------------------------------------------------
    # ENGLISH
    # --------------------------------------------------------

    if lang == "en":

        return {

            "rate": "-25%",

            "pitch": "+0Hz"
        }

    # --------------------------------------------------------
    # INTRO
    # --------------------------------------------------------

    if style == "intro":

        if energy == "high":

            return {

                "rate": "+10%",

                "pitch": "+3Hz"
            }

        if energy == "medium":

            return {

                "rate": "+5%",

                "pitch": "+1Hz"
            }

    # --------------------------------------------------------
    # CLOSING
    # --------------------------------------------------------

    if style == "closing":

        return {

            "rate": "+6%",

            "pitch": "+1Hz"
        }

    # --------------------------------------------------------
    # ENERGY
    # --------------------------------------------------------

    if energy == "high":

        return {

            "rate": "+5%",

            "pitch": "+2Hz"
        }

    if energy == "low":

        return {

            "rate": "-8%",

            "pitch": "-1Hz"
        }

    return {

        "rate": "-4%",

        "pitch": "+0Hz"
    }


# ============================================================
# SYNTHESIS
# ============================================================

async def _synthesize_async(
    text: str,
    lang: str,
    rate: str,
    pitch: str
) -> bytes:

    voice_name = (
        VOICE_EN
        if lang == "en"
        else VOICE_PT
    )
    
    fallback_voice = (
        "en-US-BrianMultilingualNeural"
        if lang == "en"
        else "pt-BR-AntonioNeural"
    )
    
    try:

        communicate = edge_tts.Communicate(

            text=text,

            voice=voice_name,

            rate=rate,

            pitch=pitch
        )

    except Exception:

        communicate = edge_tts.Communicate(

            text=text,

            voice=fallback_voice,

            rate=rate,

            pitch=pitch
        )

    buffer = io.BytesIO()

    async for chunk in communicate.stream():

        if chunk["type"] == "audio":

            buffer.write(chunk["data"])

    buffer.seek(0)

    data = buffer.read()

    if not data:

        raise RuntimeError(
            "Nenhum áudio recebido."
        )

    return data


# ============================================================
# BUILD SEGMENTS
# ============================================================

def _build_segments(
    lesson_json: dict
):

    segments = []

    repeat_en = lesson_json["repeat_each"]["en"]

    repeat_pt = lesson_json["repeat_each"]["pt"]

    # ========================================================
    # INTRO
    # ========================================================

    intro = lesson_json.get(
        "introducao",
        ""
    ).strip()

    if intro:

        intro_parts = enrich_text(
            intro
        )

        for part in intro_parts:

            voice = _resolve_voice_params(

                lang=part["lang"],

                energy=part["energy"],

                style="intro"
            )

            segments.append({

                "text": part["text"],

                "lang": part["lang"],

                "rate": voice["rate"],

                "pitch": voice["pitch"],

                "pause_ms": part["pause_ms"]
            })

        segments.append({

            "text": "",

            "pause_ms": 700
        })

    # ========================================================
    # WORD BANK
    # ========================================================

    for group in lesson_json["WORD_BANK"]:

        for index, item in enumerate(group):

            text = item["text"].strip()

            lang = item.get(
                "lang",
                "en"
            )

            pause_ms = item.get(
                "pause",
                1000
            )

            repeat = (
                repeat_en
                if lang == "en"
                else repeat_pt
            )

            is_last_pt = (
                lang == "pt"
                and index == len(group) - 1
            )

            # ------------------------------------------------
            # ENGLISH
            # ------------------------------------------------

            if lang == "en":

                for _ in range(repeat):

                    voice = _resolve_voice_params(

                        lang="en",

                        energy="medium",

                        style="english"
                    )

                    segments.append({

                        "text": text,

                        "lang": "en",

                        "rate": voice["rate"],

                        "pitch": voice["pitch"],

                        "pause_ms": 120
                    })

                segments.append({

                    "text": "",

                    "pause_ms": pause_ms
                })

                continue

            # ------------------------------------------------
            # PT ENRICHED
            # ------------------------------------------------

            context = (
                "closing"
                if is_last_pt
                else "teaching"
            )

            enriched = enrich_text(
                text,
                context=context
            )

            for _ in range(repeat):

                for part in enriched:

                    style = part["style"]

                    voice = _resolve_voice_params(

                        lang=part["lang"],

                        energy=part["energy"],

                        style=style
                    )

                    segments.append({

                        "text": part["text"],

                        "lang": part["lang"],

                        "rate": voice["rate"],

                        "pitch": voice["pitch"],

                        "pause_ms": part["pause_ms"]
                    })

            segments.append({

                "text": "",

                "pause_ms": pause_ms
            })

    return segments


# ============================================================
# RENDER
# ============================================================

async def _render_segments_async(
    segments
):

    combined = _pause(300)

    for seg in segments:

        text = seg.get(
            "text",
            ""
        )

        pause_ms = seg.get(
            "pause_ms",
            0
        )

        if text:

            audio_bytes = None

            for attempt in range(1, 4):

                try:

                    audio_bytes = await _synthesize_async(

                        text=text,

                        lang=seg["lang"],

                        rate=seg["rate"],

                        pitch=seg["pitch"]
                    )

                    break

                except Exception as e:

                    print(
                        f"⚠️ tentativa "
                        f"{attempt} falhou: {e}"
                    )

            if audio_bytes:

                audio = AudioSegment.from_file(

                    io.BytesIO(audio_bytes),

                    format="mp3"
                )

                combined += audio

            else:

                combined += _pause(900)

        if pause_ms:

            combined += _pause(
                pause_ms
            )

    return combined


# ============================================================
# MAIN
# ============================================================

def generate_audio_edge(
    lesson_json: dict,
    output_path: str
) -> str:

    print(
        "🎤 Edge TTS Multilingual"
    )

    segments = _build_segments(
        lesson_json
    )

    combined = asyncio.run(
        _render_segments_async(
            segments
        )
    )

    os.makedirs(
        os.path.dirname(output_path),
        exist_ok=True
    )

    combined.export(
        output_path,
        format="wav"
    )

    print("✔ áudio gerado")

    return output_path


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    lesson = {

        "repeat_each": {
            "pt": 1,
            "en": 2
        },

        "introducao": (
            "Fala galera! Hoje você vai aprender what's your name. Essa expressão aparece muito!"
        ),

        "WORD_BANK": [

            [

                {
                    "lang": "en",
                    "text": "what's your name"
                },

                {
                    "lang": "pt",
                    "text": (
                        "What's your name significa qual é o seu nome. Nativo usa isso direto!"
                    )
                },

                {
                    "lang": "en",
                    "text": (
                        "Hi! What's your name?"
                    )
                },

                {
                    "lang": "en",
                    "text": (
                        "I forgot what's your name."
                    )
                },

                {
                    "lang": "en",
                    "text": (
                        "Can you tell me "
                        "what's your name again?"
                    )
                },

                {
                    "lang": "pt",
                    "text": (
                        "Boa pessoal! "
                        "Agora tenta usar "
                        "what's your name "
                        "em situações reais. "
                        "See you!"
                    )
                }
            ]
        ]
    }

    generate_audio_edge(
        lesson,
        "outputs/audio/test.wav"
    )
