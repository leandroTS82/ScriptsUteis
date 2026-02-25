"""
===============================================================
 Script: MakeTermsMp3.py
 Autor: Leandro
===============================================================

Gera áudios MP3 a partir de uma lista grande de termos/frases,
com particionamento automático por tempo máximo.

ENGINES SUPORTADOS:
- gtts        (default)
- gemini_v2   (Google Gemini Speech – OFICIAL)

✅ Voices confirmadas e estáveis
Voice name	Idioma base	Característica
schedar	EN (global)	Neutra, clara, padrão
callirrhoe	EN	Mais suave / natural
despina	EN	Mais expressiva
aoede	EN	Didática / narrada
zephyr	EN	Mais rápida / dinâmica

schedar é a mais segura para estudo, cursos e listening.

🧩 Exemplo no seu script (padrão recomendado)
GEMINI_MODEL = "gemini-2.5-flash-preview-tts"
GEMINI_VOICE_NAME = "schedar"
GEMINI_SAMPLE_RATE = 24000

2️⃣ Sample Rate (indireto) ✅

Você controla no lado do cliente, ao salvar o PCM:
save_wave(..., rate=24000)
Valores comuns:
16000 → leve / speech
24000 → padrão recomendado
48000 → maior qualidade (arquivo maior)

Suporta 3 engines de TTS:
- gtts        (Google Translate)
- cloud_tts   (Google Cloud Text-to-Speech / WaveNet)
- gemini_tts  (Google Gemini Speech V2)

Configuração via JSON interno
Fallback automático: cloud_tts → gemini_tts → gtts
===============================================================
 Script: MakeTermsMp3.py
 Autor: Leandro
===============================================================

Suporta:
- gtts        (Google Translate)
- cloud_tts   (Google Cloud TTS / WaveNet)
- gemini_tts  (Google Gemini Speech V2)

Fallback configurável.
===============================================================
python MakeTermsMp3.py
"""
import os
import json
import wave
from datetime import datetime
from pydub import AudioSegment
from gtts import gTTS
from google import genai
from google.genai import types
from google.cloud import texttospeech

# =========================================================
# CORES (ANSI)
# =========================================================

RESET = "\033[0m"
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"

def log(msg, color=BLUE):
    print(f"{color}{msg}{RESET}")

def now_suffix():
    return datetime.now().strftime("%y%m%d%H%M")

# =========================================================
# PATHS
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_JSON = os.path.join(BASE_DIR, "./CreateLater/2512191115_terms_part_17.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "terms_audio")

GEMINI_KEY_PATH = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Base\FilesHelper\secret_tokens_keys\google-gemini-key.txt"
CLOUD_TTS_CREDENTIALS = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Base\FilesHelper\secret_tokens_keys\google-tts.json"

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CLOUD_TTS_CREDENTIALS

# =========================================================
# CONFIG (JSON INTERNO)
# =========================================================

TTS_CONFIG = {
    "engine": "cloud_tts",        # cloud_tts | gemini_tts | gtts
    "enable_fallback": False,      # 🔁 controla fallback
    "language": "en",
    "gender": "male",
    "voice_name": None,
    "speed": 1,
    "pause_ms": 1000,
    "repeat_each": 2,
    "max_minutes_per_mp3": 2,
    "test_mode": False,
    "test_max_minutes": 0.5,
}

# =========================================================
# VOICE MAP (Cloud TTS)
# =========================================================

VOICE_MAP = {
    ("pt", "female"): "pt-BR-Wavenet-F",
    ("pt", "male"): "pt-BR-Wavenet-B",
    ("en", "female"): "en-US-Wavenet-F",
    ("en", "male"): "en-US-Wavenet-D",
    ("es", "female"): "es-ES-Wavenet-C",
    ("es", "male"): "es-ES-Wavenet-B",
    ("fr", "female"): "fr-FR-Wavenet-C",
    ("fr", "male"): "fr-FR-Wavenet-B",
}

# =========================================================
# GEMINI CONFIG
# =========================================================

GEMINI_MODEL = "gemini-2.5-flash-preview-tts"
GEMINI_VOICE_NAME = "schedar"
GEMINI_SAMPLE_RATE = 24000

# =========================================================
# UTIL
# =========================================================

def load_gemini_key():
    return open(GEMINI_KEY_PATH, "r", encoding="utf-8").read().strip()

def save_wave(path, pcm, rate):
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(pcm)

def speed_adjust(audio, speed):
    if speed <= 1:
        return audio
    return audio.speedup(playback_speed=1 + (speed - 1) * 0.25)

def clear_temp_files():
    if not os.path.exists(OUTPUT_DIR):
        return
    for f in os.listdir(OUTPUT_DIR):
        if f.startswith("tmp_"):
            try:
                os.remove(os.path.join(OUTPUT_DIR, f))
            except:
                pass

# =========================================================
# TTS ENGINES
# =========================================================

def tts_gtts(text, cfg, tmp):
    log("→ gTTS (Google Translate)", CYAN)
    gTTS(text=text, lang=cfg["language"], slow=(cfg["speed"] == 1)).save(tmp)
    return speed_adjust(AudioSegment.from_mp3(tmp), cfg["speed"])

def tts_cloud(client, text, cfg, tmp):
    log("→ Cloud TTS (WaveNet)", CYAN)

    voice = cfg["voice_name"] or VOICE_MAP.get((cfg["language"], cfg["gender"]))
    if not voice:
        raise RuntimeError("Voice não encontrada no VOICE_MAP")

    response = client.synthesize_speech(
        input=texttospeech.SynthesisInput(text=text),
        voice=texttospeech.VoiceSelectionParams(
            language_code=voice.rsplit("-", 1)[0],
            name=voice
        ),
        audio_config=texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.0 + (cfg["speed"] - 1) * 0.15
        )
    )

    with open(tmp, "wb") as f:
        f.write(response.audio_content)

    return AudioSegment.from_mp3(tmp)

def tts_gemini(client, text, tmp):
    log("→ Gemini TTS", CYAN)

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=GEMINI_VOICE_NAME
                    )
                )
            ),
        ),
    )

    pcm = response.candidates[0].content.parts[0].inline_data.data
    save_wave(tmp, pcm, GEMINI_SAMPLE_RATE)
    return AudioSegment.from_wav(tmp)

# =========================================================
# DISPATCHER COM CONTROLE DE FALLBACK
# =========================================================

def build_tts(text, cfg, clients, tmp):
    order = ["cloud_tts", "gemini_tts", "gtts"]
    engines = order if cfg["enable_fallback"] else [cfg["engine"]]

    for engine in engines:
        try:
            log(f"Tentando engine: {engine}", YELLOW)

            if engine == "cloud_tts":
                return tts_cloud(clients["cloud"], text, cfg, tmp), engine

            if engine == "gemini_tts":
                return tts_gemini(clients["gemini"], text, tmp), engine

            return tts_gtts(text, cfg, tmp), engine

        except Exception as e:
            log(f"❌ Falha em {engine}: {e}", RED)

            if not cfg["enable_fallback"]:
                clear_temp_files()
                log("⛔ Execução interrompida (fallback desabilitado)", RED)
                raise SystemExit(1)

            log("↪ Tentando próximo engine (fallback ativo)", YELLOW)

    clear_temp_files()
    raise SystemExit("Nenhuma engine de TTS disponível")

# =========================================================
# EXECUÇÃO
# =========================================================

os.makedirs(OUTPUT_DIR, exist_ok=True)

terms = json.load(open(INPUT_JSON, "r", encoding="utf-8")).get("pending", [])
if not terms:
    log("Nenhum termo encontrado.", RED)
    raise SystemExit(0)

clients = {
    "gemini": genai.Client(api_key=load_gemini_key()),
    "cloud": texttospeech.TextToSpeechClient()
}

max_minutes = TTS_CONFIG["test_max_minutes"] if TTS_CONFIG["test_mode"] else TTS_CONFIG["max_minutes_per_mp3"]
max_ms = max_minutes * 60 * 1000

current = AudioSegment.silent(0)
engine_used_for_file = None

def export(audio, engine):
    ts = now_suffix()
    prefix = "teste_" if TTS_CONFIG["test_mode"] else ""
    name = f"{prefix}terms_{engine}_{ts}.mp3"
    path = os.path.join(OUTPUT_DIR, name)
    audio.export(path, format="mp3")
    log(f"🎧 Arquivo gerado: {path}", GREEN)

for idx, term in enumerate(terms, 1):
    log(f"\nProcessando termo {idx}: {term}", BLUE)

    tmp = os.path.join(OUTPUT_DIR, f"tmp_{idx}.audio")
    base, engine_used = build_tts(term, TTS_CONFIG, clients, tmp)

    for _ in range(TTS_CONFIG["repeat_each"]):
        trecho = base + AudioSegment.silent(TTS_CONFIG["pause_ms"])

        if len(current) + len(trecho) > max_ms:
            export(current, engine_used_for_file or engine_used)
            current = AudioSegment.silent(0)
            engine_used_for_file = None

            if TTS_CONFIG["test_mode"]:
                clear_temp_files()
                log("🧪 TEST_MODE finalizado", YELLOW)
                raise SystemExit(0)

        current += trecho
        engine_used_for_file = engine_used

if len(current) > 0:
    export(current, engine_used_for_file)

clear_temp_files()
log("✅ Concluído com sucesso", GREEN)
