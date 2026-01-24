import json
from pathlib import Path
from google import genai
from google.genai import types
from engine.project_root import get_project_root

# ============================================================
# ROOT
# ============================================================

ROOT = get_project_root()

# ============================================================
# CONFIG
# ============================================================

cfg = json.load(
    open(ROOT / "settings" / "gemini_audio.json", encoding="utf-8")
)

API_KEY_PATH = Path(cfg["api_key_path"])

if not API_KEY_PATH.exists():
    raise FileNotFoundError(f"Gemini API key não encontrada: {API_KEY_PATH}")

API_KEY = API_KEY_PATH.read_text(encoding="utf-8").strip()

client = genai.Client(api_key=API_KEY)

# ============================================================
# MAIN
# ============================================================

def generate_audio(lesson: dict, safe_word: str) -> str:
    """
    Gera áudio TTS com Gemini (SDK novo) e salva WAV.
    """
    text = " ".join(item["text"] for item in lesson["WORD_BANK"][0])

    response = client.models.generate_content(
        model=cfg["model"],
        contents=text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=cfg.get("voice", "schedar")
                    )
                )
            ),
        ),
    )

    audio_bytes = response.candidates[0].content.parts[0].inline_data.data

    output = ROOT / "media" / "audio" / f"{safe_word}.wav"
    with open(output, "wb") as f:
        f.write(audio_bytes)

    return str(output)
