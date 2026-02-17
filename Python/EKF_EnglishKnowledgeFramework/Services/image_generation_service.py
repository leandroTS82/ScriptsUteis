import os
import io
from PIL import Image

try:
    from google import genai
    from google.genai import types
except:
    genai = None


# ==========================================================
# CONFIG
# ==========================================================

DEFAULT_ASPECTS = {
    "landscape": ("16:9", (1344, 768)),
    "portrait": ("9:16", (768, 1344))
}


# ==========================================================
# SERVICE CLASS
# ==========================================================

class ImageGenerationService:

    def __init__(self, api_key: str):
        if genai is None:
            raise RuntimeError("google-genai library não instalada.")

        self.client = genai.Client(api_key=api_key)

    # ------------------------------------------------------

    def _resize_no_distortion(self, img, target_w, target_h):
        img_ratio = img.width / img.height
        tgt_ratio = target_w / target_h

        if img_ratio > tgt_ratio:
            new_height = target_h
            new_width = int(new_height * img_ratio)
        else:
            new_width = target_w
            new_height = int(new_width / img_ratio)

        img = img.resize((new_width, new_height), Image.LANCZOS)

        left = (img.width - target_w) // 2
        top = (img.height - target_h) // 2
        right = left + target_w
        bottom = top + target_h

        return img.crop((left, top, right, bottom))

    # ------------------------------------------------------

    def generate(
        self,
        prompt: str,
        output_path: str,
        mode: str = "landscape",
        reference_image: str = None,
        force_regenerate: bool = False
    ):

        if os.path.exists(output_path) and not force_regenerate:
            print("🖼 Cache encontrado:", os.path.basename(output_path))
            return output_path

        if mode not in DEFAULT_ASPECTS:
            mode = "landscape"

        aspect_ratio, (target_w, target_h) = DEFAULT_ASPECTS[mode]

        contents = [prompt]

        if reference_image and os.path.exists(reference_image):
            base_img = Image.open(reference_image)
            contents.append(base_img)

        print("🎨 Gerando imagem IA...")

        response = self.client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=contents,
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
            raise RuntimeError("Falha ao obter imagem da IA.")

        img = Image.open(io.BytesIO(raw_bytes))
        img = self._resize_no_distortion(img, target_w, target_h)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path)

        print("✔ Imagem salva:", output_path)

        return output_path
