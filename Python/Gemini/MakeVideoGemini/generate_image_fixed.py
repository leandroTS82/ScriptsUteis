# ============================================================
# generate_image_fixed.py
# Gera imagem fixa sem IA, ajustada para 16:9 ou 9:16
# ============================================================

import os
from PIL import Image

DEFAULT_ASPECTS = {
    "landscape": "16:9",
    "portrait": "9:16"
}


def resize_no_distortion(img, target_w, target_h):
    """Redimensiona mantendo proporção e corta o excesso."""
    img_ratio = img.width / img.height
    tgt_ratio = target_w / target_h

    if img_ratio > tgt_ratio:
        new_height = target_h
        new_width = int(new_height * img_ratio)
    else:
        new_width = target_w
        new_height = int(new_width / img_ratio)

    img = img.resize((new_width, new_height), Image.LANCZOS)

    # crop central
    left = (img.width - target_w) // 2
    top = (img.height - target_h) // 2
    right = left + target_w
    bottom = top + target_h

    return img.crop((left, top, right, bottom))


def generate_image_fixed(output_path, source_path, mode="landscape"):
    """
    Gera uma imagem FINAL em 16:9 a partir de uma imagem fixa.
    Não usa IA.
    """
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Imagem fixa não encontrada: {source_path}")

    print(f"🖼️ Usando imagem fixa: {source_path}")

    img = Image.open(source_path)

    aspect = DEFAULT_ASPECTS.get(mode, "16:9")

    if aspect == "16:9":
        target_w, target_h = 1344, 768
    elif aspect == "9:16":
        target_w, target_h = 768, 1344
    else:
        target_w, target_h = img.width, img.height

    final_img = resize_no_distortion(img, target_w, target_h)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    final_img.save(output_path)

    print("✔ Imagem fixa gerada em:", output_path)
    return output_path
