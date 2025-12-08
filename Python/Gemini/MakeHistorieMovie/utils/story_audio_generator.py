import os
import wave
from google import genai
from google.genai import types

API_KEY_PATH = r"C:\dev\scripts\ScriptsUteis\Python\Gemini\MakeVideoGemini\google-gemini-key.txt"

def _load_key():
    return open(API_KEY_PATH).read().strip()

def save_wave(filename, pcm, channels=1, rate=24000, sample_width=2):
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm)

def generate_story_audio(text, output_path, voice="Kore"):
    api_key = _load_key()
    client = genai.Client(api_key=api_key)

    print("🎤 Gerando áudio da história...")

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
            )
        )
    )

    pcm = response.candidates[0].content.parts[0].inline_data.data

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    save_wave(output_path, pcm)

    print("✔ Áudio salvo:", output_path)
