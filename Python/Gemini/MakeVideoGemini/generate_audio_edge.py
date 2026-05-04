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
    "en": "en-US-GuyNeural",
    # Alternativas EN: "en-US-GuyNeural", "en-US-ChristopherNeural", "en-US-EricNeural"
    "pt": "pt-BR-AntonioNeural",
    # Alternativas PT: "pt-BR-FabioNeural"
}

# False → tudo EN  |  True → voz muda conforme campo "lang"
BILINGUAL_MODE = True

# ------------------------------------------------------------------
# VELOCIDADE E TOM — ajuste fino por idioma
#
# RATE  → velocidade:  "-20%" mais lento  /  "+0%" normal  /  "+10%" mais rápido
# PITCH → tom:         "-5Hz" mais grave  /  "+0Hz" normal /  "+3Hz" mais agudo
# ------------------------------------------------------------------

RATE_CONFIG = {
    "en": "-10%",
    "pt": "+0%",
}

PITCH_CONFIG = {
    "en": "+0Hz",
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
    """
    Limpa o texto antes de enviar ao TTS.
    Remove caracteres problemáticos que causam NoAudioReceived.
    """
    # Remove traços duplos e caracteres especiais de pontuação
    text = text.replace("—", ",").replace("–", ",")
    # Remove caracteres de controle invisíveis
    text = "".join(c for c in text if c.isprintable())
    # Garante que não termina com caractere isolado problemático
    text = text.strip(" .,;:!?-")
    # Adiciona ponto final se não tiver pontuação — evita corte abrupto
    if text and text[-1] not in ".!?,":
        text += "."
    return text.strip()


async def _synthesize_async(text: str, voice: str, rate: str, pitch: str) -> bytes:
    """Sintetiza texto e retorna bytes MP3 via edge-tts."""
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
            f"Nenhum áudio recebido para o texto: '{text[:60]}'"
        )
    return data


def _synthesize_segment(text: str, lang: str) -> AudioSegment | None:
    """
    Sintetiza um segmento.
    Retorna AudioSegment ou None se falhar após retries.
    """
    voice = _get_voice(lang)
    rate  = _get_rate(lang)
    pitch = _get_pitch(lang)
    text  = _clean_text(text)

    if not text:
        return None

    # Tenta com os parâmetros originais; se falhar, tenta sem pitch (fallback)
    for attempt, (r, p) in enumerate([
        (rate, pitch),   # tentativa 1: rate + pitch configurados
        ("-10%", "+0Hz"),  # tentativa 2: mais suave, pitch neutro
        ("+0%",  "+0Hz"),  # tentativa 3: padrão absoluto
    ], start=1):
        try:
            mp3_bytes = asyncio.run(_synthesize_async(text, voice, r, p))
            return AudioSegment.from_file(io.BytesIO(mp3_bytes), format="mp3")
        except Exception as e:
            print(f"   ⚠️  tentativa {attempt} falhou ({e}) — {'retrying...' if attempt < 3 else 'pulando segmento'}")

    return None  # segmento pulado após todas as tentativas


def _pause_segment(duration_ms: int) -> AudioSegment:
    return AudioSegment.silent(duration=duration_ms)

def _split_emotional_pt_text(text: str) -> list[tuple[str, int]]:
    """
    Divide textos PT de abertura/finalização em partes menores,
    simulando efeito SSML com pausas naturais e mais emoção.
    """
    text = _clean_text(text)

    parts = re.split(r"([.!?])", text)
    result = []

    for i in range(0, len(parts), 2):
        sentence = parts[i].strip()
        punctuation = parts[i + 1] if i + 1 < len(parts) else "."

        if not sentence:
            continue

        final_text = f"{sentence}{punctuation}"

        if punctuation == "?":
            pause = 550
        elif punctuation == "!":
            pause = 420
        else:
            pause = 350

        result.append((final_text, pause))

    return result

# ------------------------------------------------------------------
# CONSTRUTOR DE SEGMENTOS
# ------------------------------------------------------------------

def _build_segments(lesson_json: dict) -> list:
    repeat_en = lesson_json["repeat_each"]["en"]
    repeat_pt = lesson_json["repeat_each"]["pt"]
    segments  = []

    intro = lesson_json.get("introducao", "").strip()
    if intro:
        for text_part, pause_ms in _split_emotional_pt_text(intro):
            segments.append({
                "text": text_part,
                "lang": "pt",
                "pause_ms": pause_ms
            })

        segments.append({"text": "", "lang": "pt", "pause_ms": 700})

    for group in lesson_json["WORD_BANK"]:
        for index, item in enumerate(group):
            text     = item["text"].strip()
            lang     = item.get("lang", "en")
            pause_ms = item.get("pause", 1000)
            repeat   = repeat_en if lang == "en" else repeat_pt

            is_final_pt = (
                lang == "pt"
                and index == len(group) - 1
            )

            if is_final_pt:
                for text_part, emotional_pause_ms in _split_emotional_pt_text(text):
                    segments.append({
                        "text": text_part,
                        "lang": "pt",
                        "pause_ms": emotional_pause_ms
                    })

                segments.append({
                    "text": "",
                    "lang": "pt",
                    "pause_ms": pause_ms
                })

                continue

            for _ in range(repeat):
                segments.append({"text": text, "lang": lang, "pause_ms": 0})

            segments.append({"text": "", "lang": lang, "pause_ms": pause_ms})

    return segments


# ------------------------------------------------------------------
# FUNÇÃO PRINCIPAL
# ------------------------------------------------------------------

def generate_audio_edge(lesson_json: dict, output_path: str) -> str:
    print("🎤 [Edge TTS] Iniciando geração de áudio...")
    print(f"   Bilíngue : {'ATIVO' if BILINGUAL_MODE else 'DESATIVADO (tudo EN)'}")
    print(f"   Voz EN   : {VOICE_CONFIG['en']}  rate={RATE_CONFIG['en']}  pitch={PITCH_CONFIG['en']}")
    print(f"   Voz PT   : {VOICE_CONFIG['pt']}  rate={RATE_CONFIG['pt']}  pitch={PITCH_CONFIG['pt']}")

    segments = _build_segments(lesson_json)
    combined = AudioSegment.silent(duration=300)

    for i, seg in enumerate(segments):
        text     = seg["text"]
        lang     = seg["lang"]
        pause_ms = seg["pause_ms"]

        if text:
            preview = text[:60] + ("..." if len(text) > 60 else "")
            print(f"   [{i+1}/{len(segments)}] [{lang.upper()}] {preview}")
            audio_seg = _synthesize_segment(text, lang)
            if audio_seg:
                combined += audio_seg
            else:
                print(f"   ⚠️  Segmento pulado — substituído por silêncio de 800ms")
                combined += _pause_segment(800)

        if pause_ms > 0:
            combined += _pause_segment(pause_ms)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    combined.export(output_path, format="wav")

    duration_s = len(combined) / 1000
    print(f"✔  Áudio Edge TTS salvo em: {output_path}  ({duration_s:.1f}s)")
    return output_path


# ------------------------------------------------------------------
# TESTE RÁPIDO
# ------------------------------------------------------------------

if __name__ == "__main__":
    _test_lesson = {
        "repeat_each": {"pt": 1, "en": 2},
        "introducao": "Hey everyone! Today we learn the word resilient.",
        "nome_arquivos": "resilient",
        "WORD_BANK": [
            [
                {"lang": "en", "text": "resilient",                                "pause": 1000},
                {"lang": "pt", "text": "Resiliente, que se recupera facilmente."},
                {"lang": "en", "text": "She is very resilient after hard times.",  "pause": 1000},
                {"lang": "en", "text": "Resilient people never give up easily.",   "pause": 1000},
                {"lang": "en", "text": "Being resilient helps you grow stronger.", "pause": 1500},
                {"lang": "pt", "text": "Continue praticando! Voce esta arrasando."},
            ]
        ]
    }
    os.makedirs("outputs/audio", exist_ok=True)
    generate_audio_edge(_test_lesson, "outputs/audio/test_edge.wav")