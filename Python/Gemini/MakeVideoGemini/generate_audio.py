import os
import wave
from google import genai
from google.genai import types

API_KEY_PATH = "C:\\dev\\scripts\\ScriptsUteis\\Python\\secret_tokens_keys\\google-gemini-key.txt"


def load_api_key():
    if not os.path.exists(API_KEY_PATH):
        raise FileNotFoundError(f"API Key não encontrada: {API_KEY_PATH}")
    return open(API_KEY_PATH, "r").read().strip()


def save_wave(filename, pcm, channels=1, rate=24000, sample_width=2):
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm)


def generate_audio(text, output_path, voice="schedar"):
    """
    Gera áudio com Gemini TTS.
    """

    api_key = load_api_key()
    client = genai.Client(api_key=api_key)

    print(f"🎤 Gerando áudio com Gemini (TTS)... Voz: {voice}")

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

    pcm_data = response.candidates[0].content.parts[0].inline_data.data

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    save_wave(output_path, pcm_data)

    print("✔ Áudio salvo em:", output_path)
