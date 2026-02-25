import os
import io
from google import genai
from google.genai import types
from PIL import Image

API_KEY_PATH = "C:\\Users\\leand\\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\\EKF - English Knowledge Framework - Base\\FilesHelper\\secret_tokens_keys\\google-gemini-key.txt"

DEFAULT_IMAGE_ASPECTS = {
    "landscape": "16:9",
    "portrait": "9:16"
}

DEFAULT_LEANDRINHO = "assets/default_bg.png"


# --------------------------------------------------------
# Helpers
# --------------------------------------------------------

def load_api_key():
    if not os.path.exists(API_KEY_PATH):
        raise FileNotFoundError(f"API Key não encontrada: {API_KEY_PATH}")
    return open(API_KEY_PATH, "r").read().strip()


def resize_no_distortion(img, target_w, target_h):
    """Redimensiona sem distorção."""
    img_ratio = img.width / img.height
    tgt_ratio = target_w / target_h

    if img_ratio > tgt_ratio:
        new_height = target_h
        new_width = int(new_height * img_ratio)
    else:
        new_width = target_w
        new_height = int(new_width / img_ratio)

    img = img.resize((new_width, new_height), Image.LANCZOS)

    # Crop central
    left = (img.width - target_w) // 2
    top = (img.height - target_h) // 2
    right = left + target_w
    bottom = top + target_h

    return img.crop((left, top, right, bottom))


# --------------------------------------------------------
# MAIN IMAGE GENERATOR
# --------------------------------------------------------

def generate_image(word, output_path, mode="landscape"):
    """
    Gera imagem baseada no personagem Leandrinho (default_bg.png)
    usando IA Gemini 2.5 Flash Image.
    """

    api_key = load_api_key()
    client = genai.Client(api_key=api_key)

    if not os.path.exists(DEFAULT_LEANDRINHO):
        raise FileNotFoundError("Imagem base do Leandrinho não encontrada.")

    base_img = Image.open(DEFAULT_LEANDRINHO)

    aspect_ratio = DEFAULT_IMAGE_ASPECTS.get(mode, "16:9")

    prompt = (
        f"Generate a vibrant and friendly educational {mode} thumbnail featuring "
        f"Leandrinho, an upbeat Brazilian English teacher who uses technology. "
        f"The theme must clearly show the meaning of '{word}'. "
        f"Leandrinho must be smiling, expressive, confident, and teaching. "
        f"Preserve the character identity from the reference image but allow changes "
        f"in pose, expression, background, lighting, and composition."
        f"In The bellow part, footer of the image add the youtube logo subscriber and text asking to like and subscribe to the channel using the theme style (in potuguese)"
    )

    print("🧠 Gerando imagem com IA (Gemini Flash Image)...")

    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=[prompt, base_img],
        config=types.GenerateContentConfig(
            image_config=types.ImageConfig(
                aspect_ratio=aspect_ratio
            )
        )
    )

    raw_bytes = None

    for part in response.parts:
        if part.inline_data is not None:
            raw_bytes = part.inline_data.data

    if raw_bytes is None:
        raise RuntimeError("Não foi possível obter dados da imagem gerada.")

    # Converter para PIL
    final_img = Image.open(io.BytesIO(raw_bytes))

    # Ajustar dimensões finais com base na resolução oficial
    if aspect_ratio == "16:9":
        target_w, target_h = 1344, 768
    elif aspect_ratio == "9:16":
        target_w, target_h = 768, 1344
    else:
        target_w, target_h = final_img.width, final_img.height

    final_img = resize_no_distortion(final_img, target_w, target_h)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    final_img.save(output_path)

    print("✔ Imagem final gerada e salva em:", output_path)
    return output_path
