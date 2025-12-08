import os
import io
from PIL import Image
from google import genai
from google.genai import types
from groq import Groq


DEFAULT_IMAGE = "assets/default_bg.png"
DEFAULT_GIF = "assets/default.gif"

GEMINI_KEY = r"C:\dev\scripts\ScriptsUteis\Python\Gemini\MakeVideoGemini\google-gemini-key.txt"
GROQ_KEY = r"C:\dev\scripts\ScriptsUteis\Python\Gemini\MakeVideoGemini\groq_api_key.txt"


def _load_key(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Chave não encontrada: {path}")
    return open(path).read().strip()


# =====================================================
# 1. Tentar gerar imagem com Gemini
# =====================================================
def try_gemini_image(prompt):
    try:
        api_key = _load_key(GEMINI_KEY)
        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=prompt
        )

        for part in response.parts:
            if part.inline_data:
                return part.inline_data.data

        return None
    except Exception as e:
        print("⚠ Gemini image falhou:", e)
        return None


# =====================================================
# 2. Tentar gerar imagem com Groq
# =====================================================
def try_groq_image(prompt):
    try:
        api = _load_key(GROQ_KEY)
        client = Groq(api_key=api)

        response = client.images.generate(
            model="luma-flux-schnell",
            prompt=prompt,
            size="1024x576"
        )

        if hasattr(response, "image_base64"):
            import base64
            return base64.b64decode(response.image_base64)

        return None
    except Exception as e:
        print("⚠ Groq image falhou:", e)
        return None


# =====================================================
# 3. Função principal: imagem ou GIF
# =====================================================
def generate_story_image_or_gif(story_text, safe_name):
    prompt = (
        "Generate an illustrated scenic thumbnail representing this story: "
        f"\"{story_text}\". Style: cinematic, soft lighting, emotional, expressive, 16:9."
    )

    print("🧠 Tentando gerar imagem com Gemini...")
    result = try_gemini_image(prompt)

    if not result:
        print("⚠ Tentando gerar imagem com Groq...")
        result = try_groq_image(prompt)

    # Fallback
    if not result:
        print("⚠ Falha geral na geração → usando imagem padrão.")
        return DEFAULT_IMAGE

    # Salvar imagem gerada
    output_path = f"outputs/images/{safe_name}.png"
    with open(output_path, "wb") as f:
        f.write(result)

    print("✔ Imagem gerada:", output_path)
    return output_path
