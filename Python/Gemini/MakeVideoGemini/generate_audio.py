import os
import wave
import base64

from google import genai
from google.genai import types

API_KEY_PATH = "../google-gemini-key.txt"


def load_api_key():
    if not os.path.exists(API_KEY_PATH):
        raise FileNotFoundError(f"API Key não encontrada: {API_KEY_PATH}")
    return open(API_KEY_PATH, "r").read().strip()


def save_wave(filename, pcm, channels=1, rate=24000, sample_width=2):
    """Salva áudio PCM em formato WAV."""
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm)


def generate_audio(text, output_path, voice="Kore"):
    """
    Geração de áudio utilizando:
    - Modelo: gemini-2.5-flash-preview-tts
    - Configuração oficial da documentação Google
    """

    api_key = load_api_key()

    client = genai.Client(api_key=api_key)

    print("🎤 Gerando áudio com gemini-2.5-flash-preview-tts...")

    response = client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents=text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=voice
                    )
                )
            ),
        ),
    )

    # A resposta é PCM inline
    pcm_data = response.candidates[0].content.parts[0].inline_data.data

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    save_wave(output_path, pcm_data)

    print("✔ Áudio salvo em:", output_path)
