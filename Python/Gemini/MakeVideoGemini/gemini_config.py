import os
import google.generativeai as genai

class GeminiConfig:

    def __init__(self, key_path="../google-gemini-key.txt"):
        # usa a chave do diretório Python/Gemini
        self.key_path = key_path
        self.api_key = self._load_key()
        self._configure_sdk()

        self.MODEL_TEXT = "gemini-3-pro-preview"
        self.MODEL_AUDIO = "gemini-3-pro-preview"

    def _load_key(self):
        if not os.path.exists(self.key_path):
            raise FileNotFoundError(f"[ERRO] Key não encontrada: {self.key_path}")
        return open(self.key_path).read().strip()

    def _configure_sdk(self):
        genai.configure(api_key=self.api_key)

    def get_text(self):
        return genai.GenerativeModel(self.MODEL_TEXT)

    def get_audio(self):
        return genai.GenerativeModel(self.MODEL_AUDIO)
