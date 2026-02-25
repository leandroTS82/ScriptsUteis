import os
import io
import base64
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
from google import genai
from google.genai import types
from groq import Groq


# ============================================
# CONFIGURAÇÕES
# ============================================

DEFAULT_IMAGE = r"C:\dev\scripts\ScriptsUteis\Python\Gemini\MakeVideoGemini\assets\default_bg.png"
GEMINI_KEY = "C:\\Users\\leand\\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\\EKF - English Knowledge Framework - Base\\FilesHelper\\secret_tokens_keys\\google-gemini-key.txt"
GROQ_KEY = "C:\\Users\\leand\\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\\EKF - English Knowledge Framework - Base\\FilesHelper\\secret_tokens_keys\\groq_api_key.txt"

TARGET_W = 1344
TARGET_H = 768

BADGE_SIZE_RATIO = 0.22
BADGE_PADDING = 25  # distância das bordas


# ============================================
# HELPERS
# ============================================

def _load_key(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Chave não encontrada: {path}")
    return open(path).read().strip()


def resize_no_distortion(img, target_w, target_h):
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
    return img.crop((left, top, left + target_w, top + target_h))


# ============================================
# REMOVER FUNDO DE IMAGEM (SEM OPENCV)
# ============================================

def remove_background(pil_img):
    img = pil_img.convert("RGBA")
    datas = img.getdata()

    new_data = []
    for pixel in datas:
        r, g, b, a = pixel

        # remove branco ou quase branco
        if r > 230 and g > 230 and b > 230:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(pixel)

    img.putdata(new_data)
    return img


# ============================================
# GEMINI - IMAGEM PRINCIPAL
# ============================================

def try_gemini_main_image(prompt):
    try:
        client = genai.Client(api_key=_load_key(GEMINI_KEY))

        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=prompt,
            config=types.GenerateContentConfig(
                image_config=types.ImageConfig(aspect_ratio="16:9")
            )
        )

        for part in response.candidates[0].content.parts:
            if hasattr(part, "inline_data") and part.inline_data:
                return part.inline_data.data

    except Exception as e:
        print("⚠ Gemini main image falhou:", e)
    return None


# ============================================
# GERAÇÃO DO LEANDRINHO (SELO)
# ============================================

def generate_leandrinho_variant(story_text):
    base_img = Image.open(DEFAULT_IMAGE).convert("RGBA")

    prompt = (
        "Generate a holographic-style narrator badge of Leandrinho, the friendly Brazilian English teacher. "
        "He should appear expressive, smiling, and actively presenting the story. "
        "Add a soft blue glow around the character for a tech hologram effect. "
        "Keep the background fully transparent. Pose should adapt to the story theme.\n\n"
        f"Story: {story_text}"
    )

    try:
        client = genai.Client(api_key=_load_key(GEMINI_KEY))
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[prompt, base_img],
            config=types.GenerateContentConfig(
                image_config=types.ImageConfig(aspect_ratio="1:1")
            )
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data:
                raw = part.inline_data.data
                badge = Image.open(io.BytesIO(raw)).convert("RGBA")
                return remove_background(badge)

    except Exception as e:
        print("⚠ Erro ao gerar variant do Leandrinho:", e)

    return base_img


# ============================================
# TÍTULO ESTILO YOUTUBE
# ============================================

def apply_title(img, title):
    draw = ImageDraw.Draw(img)
    title = " ".join(title.split())

    try:
        font = ImageFont.truetype("impact.ttf", 86)
    except:
        font = ImageFont.truetype("arialbd.ttf", 86)

    try:
        tw = draw.textlength(title, font=font)
    except:
        tw = len(title) * 20

    x = (img.width - tw) // 2
    y = 25

    # contorno forte estilo YouTube
    for dx in range(-4, 5):
        for dy in range(-4, 5):
            draw.text((x+dx, y+dy), title, font=font, fill="black")

    draw.text((x, y), title, font=font, fill="white")

    return img


# ============================================
# ADICIONAR LEANDRINHO — CANTO SUPERIOR DIREITO
# ============================================

def add_leandrinho_badge(img, story_text):
    badge = generate_leandrinho_variant(story_text)

    # tamanho proporcional
    badge_w = int(TARGET_W * BADGE_SIZE_RATIO)
    badge_h = int(badge_w * (badge.height / badge.width))
    badge = badge.resize((badge_w, badge_h), Image.LANCZOS)

    # glow holográfico
    glow = Image.new("RGBA", (badge_w + 40, badge_h + 40), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse(
        [0, 0, badge_w + 40, badge_h + 40],
        fill=(0, 180, 255, 85)
    )
    glow = glow.filter(ImageFilter.GaussianBlur(18))

    # POSICIONAMENTO — TOPO DIREITO
    pos_x = TARGET_W - badge_w - BADGE_PADDING
    pos_y = BADGE_PADDING

    img.alpha_composite(glow, (pos_x - 20, pos_y - 20))
    img.alpha_composite(badge, (pos_x, pos_y))

    return img


# ============================================
# FUNÇÃO PRINCIPAL
# ============================================

def generate_story_image_or_gif(story_text, safe_name, final_title):
    prompt = (
        "Create a modern cinematic illustration in the visual style of the Miles Morales (with afro american people)"
        "animated universe (Spider-Verse). Use expressive characters, vibrant lighting, "
        "dynamic posing and a comic-film texture. "
        "Represent the story below WITHOUT including the narrator. "
        "Leave free space on the top-right area for a holographic badge narrator.\n\n"
        f"{story_text}"
    )

    print("🧠 Gerando imagem principal...")
    result = try_gemini_main_image(prompt)

    if not result:
        print("⚠ Usando imagem padrão")
        img = Image.open(DEFAULT_IMAGE).convert("RGBA").resize((TARGET_W, TARGET_H))
    else:
        img = Image.open(io.BytesIO(result)).convert("RGBA")
        img = resize_no_distortion(img, TARGET_W, TARGET_H)

    # Título estilo YouTube
    img = apply_title(img, final_title)

    # Leandrinho no topo direito
    img = add_leandrinho_badge(img, story_text)

    # Salvar
    output_path = f"outputs/images/{safe_name}.png"
    os.makedirs("outputs/images", exist_ok=True)
    img.save(output_path, "PNG")

    print("✔ Imagem gerada:", output_path)
    return output_path
