import os
import random
from PIL import Image

RANDOM_IMAGE_DIR = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\LeanndrinhoDefaultImage"


def _get_random_image_path() -> str:
    if not os.path.exists(RANDOM_IMAGE_DIR):
        raise FileNotFoundError(
            f"[generate_image_zero_cost] Diretório não encontrado: {RANDOM_IMAGE_DIR}"
        )

    files = [
        os.path.join(RANDOM_IMAGE_DIR, f)
        for f in os.listdir(RANDOM_IMAGE_DIR)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ]

    if not files:
        raise FileNotFoundError(
            f"[generate_image_zero_cost] Nenhuma imagem válida encontrada em: {RANDOM_IMAGE_DIR}"
        )

    return random.choice(files)


def generate_image_zero_cost(
    output_path: str,
    mode: str = "landscape"
) -> str:
    """
    Copia imagem aleatória do diretório para o output sem redimensionar.
    Sempre em modo paisagem.
    """

    source_path = _get_random_image_path()

    print(f"🖼️  [ZeroCost] Usando imagem aleatória: {source_path}")
    print(f"   Modo: landscape (sem redimensionamento)")

    img = Image.open(source_path).convert("RGB")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path)

    print(f"✔  Imagem zero-cost salva em: {output_path}")
    return output_path