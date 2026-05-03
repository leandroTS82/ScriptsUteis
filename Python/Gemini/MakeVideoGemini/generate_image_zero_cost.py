# ============================================================
# generate_image_zero_cost.py
# Gera imagem de fundo sem usar IA (zero custo de API).
# Usa a imagem fixa em assets/ e redimensiona para o modo
# solicitado (landscape 16:9 ou portrait 9:16).
#
# Chamado automaticamente quando USE_ZERO_COST_IMAGE = True
# em main.py — substitui o generate_image.py (Gemini IA).
# ============================================================

import os
from PIL import Image

# ----------------------------------------------------------
# Imagem fixa padrão (mesma usada como referência pelo Gemini)
# ----------------------------------------------------------
DEFAULT_FIXED_IMAGE = os.path.join(
    os.path.dirname(__file__), "assets", "default_bg.png"
)

ASPECT_RESOLUTIONS = {
    "landscape": (1344, 768),   # 16:9
    "portrait":  (768, 1344),   # 9:16
}


def _resize_no_distortion(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """
    Redimensiona mantendo proporção original e faz crop central
    para encaixar exatamente nas dimensões alvo — sem distorção.
    """
    img_ratio = img.width / img.height
    tgt_ratio = target_w / target_h

    if img_ratio > tgt_ratio:
        new_height = target_h
        new_width = int(new_height * img_ratio)
    else:
        new_width = target_w
        new_height = int(new_width / img_ratio)

    img = img.resize((new_width, new_height), Image.LANCZOS)

    left  = (img.width  - target_w) // 2
    top   = (img.height - target_h) // 2
    right = left + target_w
    bottom = top + target_h

    return img.crop((left, top, right, bottom))


def generate_image_zero_cost(
    output_path: str,
    source_path: str = DEFAULT_FIXED_IMAGE,
    mode: str = "landscape"
) -> str:
    """
    Copia/redimensiona a imagem fixa para o caminho de saída,
    mantendo o mesmo padrão de dimensões do fluxo com IA.

    Parâmetros
    ----------
    output_path : str
        Caminho completo onde o PNG final será salvo.
    source_path : str
        Imagem de origem (default: assets/default_bg.png).
    mode : str
        "landscape" (16:9) ou "portrait" (9:16).

    Retorna
    -------
    str : output_path confirmado.
    """

    if not os.path.exists(source_path):
        raise FileNotFoundError(
            f"[generate_image_zero_cost] Imagem fixa não encontrada: {source_path}"
        )

    target_w, target_h = ASPECT_RESOLUTIONS.get(mode, ASPECT_RESOLUTIONS["landscape"])

    print(f"🖼️  [ZeroCost] Usando imagem fixa: {source_path}")
    print(f"   Modo: {mode}  →  {target_w}x{target_h}px")

    img = Image.open(source_path).convert("RGB")
    img = _resize_no_distortion(img, target_w, target_h)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path)

    print(f"✔  Imagem zero-cost salva em: {output_path}")
    return output_path