import io
import os
from PIL import Image
from google import genai
from google.genai import types

BASE_BADGE_IMAGE = os.path.join(
    os.path.dirname(__file__),
    "..",
    "assets",
    "leandrinho_base.png"
)

def generate_badge(client, prompt: str) -> Image.Image:
    """
    Gera o selo do Leandrinho usando:
    - imagem base fixa (branding)
    - Gemini apenas como variação guiada
    """

    if not os.path.exists(BASE_BADGE_IMAGE):
        raise FileNotFoundError(f"Imagem base não encontrada: {BASE_BADGE_IMAGE}")

    base_img = Image.open(BASE_BADGE_IMAGE).convert("RGBA")

    response = client.client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=[prompt, base_img],
        config=types.GenerateContentConfig(
            image_config=types.ImageConfig(aspect_ratio="1:1")
        )
    )

    for part in response.candidates[0].content.parts:
        if part.inline_data:
            return Image.open(io.BytesIO(part.inline_data.data)).convert("RGBA")

    raise RuntimeError("Gemini não retornou imagem para o selo")
