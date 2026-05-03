# ============================================================
# generate_audio_gcloud.py
# Geração de áudio via Google Cloud Text-to-Speech.
#
# Chamado automaticamente quando USE_GCLOUD_AUDIO = True
# em main.py — substitui o generate_audio.py (Gemini TTS).
#
# Preparado para escalar para bilíngue (EN + PT) no futuro:
# cada item do WORD_BANK tem "lang" → já respeitamos aqui,
# mas por enquanto TUDO é gerado em EN masculino (ver config).
#
# Dependência:
#   pip install google-cloud-texttospeech pydub
#
# Autenticação Google Cloud (uma das opções):
#   a) Variável de ambiente: GOOGLE_APPLICATION_CREDENTIALS=<path>.json
#   b) Caminho direto: GCLOUD_KEY_PATH (var abaixo)
# ============================================================

import os
import json
import wave
import io
from pydub import AudioSegment

# ----------------------------------------------------------
# CONFIGURAÇÃO
# ----------------------------------------------------------

GCLOUD_KEY_PATH = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Base\FilesHelper\secret_tokens_keys\google-cloud-tts-key.json"

# ----------------------------------------------------------
# MAPEAMENTO DE VOZES POR IDIOMA
# Preparado para bilíngue futuro.
# Chave: lang code  →  (language_code, voice_name, ssml_gender)
# ----------------------------------------------------------
VOICE_CONFIG = {
    # ── Inglês (padrão atual) ─────────────────────────────
    "en": {
        "language_code": "en-US",
        "voice_name":    "en-US-Neural2-D",   # masculino, natural
        "ssml_gender":   "MALE",
    },
    # ── Português (preparado para o futuro) ───────────────
    "pt": {
        "language_code": "pt-BR",
        "voice_name":    "pt-BR-Neural2-B",   # masculino, natural
        "ssml_gender":   "MALE",
    },
}

# Enquanto geração bilíngue não está ativa, TUDO usa EN.
# Quando quiser ativar bilíngue, mude para True.
BILINGUAL_MODE = False


# ----------------------------------------------------------
# HELPERS
# ----------------------------------------------------------

def _load_client():
    """Instancia o cliente Google Cloud TTS."""
    from google.cloud import texttospeech

    if GCLOUD_KEY_PATH and os.path.exists(GCLOUD_KEY_PATH):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GCLOUD_KEY_PATH

    return texttospeech.TextToSpeechClient()


def _synthesize_segment(client, text: str, lang: str) -> bytes:
    """
    Sintetiza um trecho de texto e retorna bytes WAV (LINEAR16, 24 kHz).

    lang : "en" ou "pt"
           Em modo monolíngue, sempre usa "en".
    """
    from google.cloud import texttospeech

    effective_lang = lang if BILINGUAL_MODE else "en"
    cfg = VOICE_CONFIG[effective_lang]

    # Detecta SSML vs texto puro
    if text.strip().startswith("<speak"):
        input_obj = texttospeech.SynthesisInput(ssml=text)
    else:
        input_obj = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code=cfg["language_code"],
        name=cfg["voice_name"],
        ssml_gender=getattr(texttospeech.SsmlVoiceGender, cfg["ssml_gender"]),
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16,
        sample_rate_hertz=24000,
    )

    response = client.synthesize_speech(
        input=input_obj,
        voice=voice,
        audio_config=audio_config,
    )

    return response.audio_content  # bytes WAV


def _pause_wav(duration_ms: int, sample_rate: int = 24000) -> bytes:
    """Gera bytes WAV de silêncio com a duração solicitada (ms)."""
    num_samples = int(sample_rate * duration_ms / 1000)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"\x00\x00" * num_samples)
    return buf.getvalue()


def _wav_bytes_to_segment(wav_bytes: bytes) -> AudioSegment:
    """Converte bytes WAV para AudioSegment do pydub."""
    return AudioSegment.from_file(io.BytesIO(wav_bytes), format="wav")


# ----------------------------------------------------------
# CONSTRUTOR DE TEXTO SEGMENTADO A PARTIR DO lesson_json
# ----------------------------------------------------------

def _build_segments(lesson_json: dict) -> list[dict]:
    """
    Converte lesson_json em lista de segmentos:
      [{"text": str, "lang": str, "pause_ms": int}, ...]

    Respeita repeat_each: cada item EN repete N vezes, PT repete M vezes.
    Preparado para bilíngue: mantém o campo lang em cada segmento.
    """
    repeat_en = lesson_json["repeat_each"]["en"]
    repeat_pt = lesson_json["repeat_each"]["pt"]

    segments = []

    # Introdução (1 vez, em EN por padrão)
    intro = lesson_json.get("introducao", "").strip()
    if intro:
        segments.append({"text": intro, "lang": "en", "pause_ms": 1000})

    for group in lesson_json["WORD_BANK"]:
        for item in group:
            text     = item["text"].strip()
            lang     = item.get("lang", "en")
            pause_ms = item.get("pause", 1000)
            repeat   = repeat_en if lang == "en" else repeat_pt

            for _ in range(repeat):
                segments.append({"text": text, "lang": lang, "pause_ms": 0})

            # pausa após as repetições
            segments.append({"text": "", "lang": lang, "pause_ms": pause_ms})

    return segments


# ----------------------------------------------------------
# FUNÇÃO PRINCIPAL
# ----------------------------------------------------------

def generate_audio_gcloud(lesson_json: dict, output_path: str) -> str:
    """
    Gera áudio completo da aula usando Google Cloud TTS
    e salva como WAV em output_path.

    Parâmetros
    ----------
    lesson_json : dict
        JSON da aula (gerado por generate_script.py).
    output_path : str
        Caminho de saída do arquivo .wav.

    Retorna
    -------
    str : output_path confirmado.
    """

    print("🎤 [GCloud TTS] Iniciando geração de áudio...")
    print(f"   Modo bilíngue: {'ATIVO' if BILINGUAL_MODE else 'DESATIVADO (tudo em EN)'}")

    client   = _load_client()
    segments = _build_segments(lesson_json)

    combined = AudioSegment.silent(duration=300)  # pequeno silêncio inicial

    for i, seg in enumerate(segments):
        text     = seg["text"]
        lang     = seg["lang"]
        pause_ms = seg["pause_ms"]

        if text:
            print(f"   [{i+1}/{len(segments)}] [{lang.upper()}] {text[:60]}{'...' if len(text) > 60 else ''}")
            wav_bytes = _synthesize_segment(client, text, lang)
            audio_seg = _wav_bytes_to_segment(wav_bytes)
            combined += audio_seg

        if pause_ms > 0:
            combined += AudioSegment.silent(duration=pause_ms)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    combined.export(output_path, format="wav")

    duration_s = len(combined) / 1000
    print(f"✔  Áudio GCloud salvo em: {output_path}  ({duration_s:.1f}s)")
    return output_path


# ----------------------------------------------------------
# TESTE RÁPIDO (python generate_audio_gcloud.py)
# ----------------------------------------------------------

if __name__ == "__main__":
    _test_lesson = {
        "repeat_each": {"pt": 1, "en": 2},
        "introducao": "Hey everyone! Today we are going to learn the word 'resilient'.",
        "nome_arquivos": "resilient",
        "WORD_BANK": [
            [
                {"lang": "en", "text": "resilient",                               "pause": 1000},
                {"lang": "pt", "text": "Resiliente — que se recupera facilmente."},
                {"lang": "en", "text": "She is very resilient after hard times.", "pause": 1000},
                {"lang": "en", "text": "Resilient people never give up easily.", "pause": 1000},
                {"lang": "en", "text": "Being resilient helps you grow stronger.", "pause": 1500},
                {"lang": "pt", "text": "Continue praticando! Você está arrasando."},
            ]
        ]
    }

    generate_audio_gcloud(_test_lesson, "outputs/audio/test_gcloud.wav")