from google import genai
from google.genai import types

class GeminiClient:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    def generate_audio(self, text: str, voice="Charon") -> bytes:
        response = self.client.models.generate_content(
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
        return response.candidates[0].content.parts[0].inline_data.data

    def generate_image(self, prompt: str) -> bytes:
        response = self.client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=prompt,
            config=types.GenerateContentConfig(
                image_config=types.ImageConfig(aspect_ratio="16:9")
            )
        )
        for p in response.candidates[0].content.parts:
            if p.inline_data:
                return p.inline_data.data
        raise RuntimeError("Gemini did not return image bytes")
