from google import genai
from google.genai import types

class GeminiClient:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    def generate_audio(self, text: str, instruction: str = "") -> bytes:
        final_text = f"{instruction}\n\n{text}" if instruction else text

        response = self.client.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=final_text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"]
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
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                return part.inline_data.data
        raise RuntimeError("No image returned")

    def generate_text(self, prompt: str) -> str:
        res = self.client.models.generate_content(
            model="gemini-2.0-flash-lite-preview",
            contents=prompt
        )
        return res.text
