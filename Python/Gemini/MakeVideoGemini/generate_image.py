import base64
import os
from gemini_config import GeminiConfig
from groq_config import GroqConfig

DEFAULT_IMG = "assets/default_bg.png"


def try_gemini_image(word, output_path):
    print("🔹 Tentando gerar imagem via Gemini...")
    try:
        config = GeminiConfig()
        model = config.get_image()

        prompt = f"""
        Create an HD YouTube thumbnail for the English word '{word}'.
        Bright, modern, colorful, 16:9, educational.
        """

        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "image/png"}
        )

        img_bytes = response.candidates[0].content.parts[0].data

        with open(output_path, "wb") as f:
            f.write(img_bytes)

        print("✅ Imagem gerada via Gemini!")
        return True

    except Exception as e:
        print(f"⚠️ Gemini falhou: {e}")
        return False



def try_groq_image(word, output_path):
    print("🔹 Tentando gerar imagem via Groq (SDXL)...")
    try:
        config = GroqConfig()
        client = config.client

        prompt = f"Bright HD thumbnail for English lesson about '{word}'."

        result = client.images.generate(
            model="stable-diffusion-xl",
            prompt=prompt,
            size="1024x1024"
        )

        img_b64 = result.data[0].b64_json
        img_bytes = base64.b64decode(img_b64)

        with open(output_path, "wb") as f:
            f.write(img_bytes)

        print("✅ Imagem gerada via Groq!")
        return True

    except Exception as e:
        print(f"⚠️ Groq falhou: {e}")
        return False



def use_default_image(output_path):
    print("🔸 Usando imagem padrão (fallback final).")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(DEFAULT_IMG, "rb") as src:
        with open(output_path, "wb") as dst:
            dst.write(src.read())
    print("✅ Imagem padrão copiada.")
    return True



def generate_image(word, output_path):
    print("📌 Iniciando geração de imagem...")

    if try_gemini_image(word, output_path):
        return

    if try_groq_image(word, output_path):
        return

    use_default_image(output_path)
