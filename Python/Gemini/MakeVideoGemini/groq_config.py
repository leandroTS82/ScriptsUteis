import os
from groq import Groq

class GroqConfig:

    def __init__(self, key_path="C:\\Users\\leand\\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\\LTS SP Site - Documentos de estudo de inglês\\FilesHelper\\secret_tokens_keys\\groq_api_key.txt"):
        self.key_path = key_path
        self.api_key = self._load_key()
        self.client = Groq(api_key=self.api_key)

    def _load_key(self):
        if not os.path.exists(self.key_path):
            raise FileNotFoundError(f"[ERRO] Groq API Key não encontrada: {self.key_path}")
        return open(self.key_path).read().strip()
