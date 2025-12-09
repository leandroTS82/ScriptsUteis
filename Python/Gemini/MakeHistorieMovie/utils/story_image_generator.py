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
GEMINI_KEY = r"C:\dev\scripts\ScriptsUteis\Python\Gemini\MakeVideoGemini\google-gemini-key.txt"
GROQ_KEY = r"C:\dev\scripts\ScriptsUteis\Python\Gemini\MakeVideoGemini\groq_api_key.txt"

TARGET_W = 1344
TARGET_H = 768

BADGE_SIZE_RATIO = 0.22
BADGE_PADDING = 25


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
# REMOÇÃO DE FUNDO SEM OPENCV (Pillow Only)
# ============================================

def remove_background(pil_img):
    img = pil_img.convert("RGBA")
    datas = img.getdata()

    new_data = []
    for pixel in datas:
        r, g, b, a = pixel

        # considera branco / quase branco como fundo
        if r > 230 and g > 230 and b > 230:
            new_data.append((255, 255, 255, 0))  # transparente
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
        return None

    except Exception as e:
        print("⚠ Gemini main image falhou:", e)
        return None


# ============================================
# GERAÇÃO DO LEANDRINHO VARIANTE
# ============================================

def generate_leandrinho_variant(story_text):
    base_img = Image.open(DEFAULT_IMAGE).convert("RGBA")

    prompt = (
        "Generate a small holographic-style badge illustration of Leandrinho, "
        "the friendly Brazilian English teacher. "
        "He should have a dynamic, expressive posture matching the story above right.\n\n"
        f"Story: {story_text}\n\n"
        "Rules:\n"
        "- Maintain character identity.\n"
        "- Add soft blue glow (tech hologram).\n"
        "- tech hologram like Iron man movies or doctor strange, but keep the theme style and context.\n"
        "- Add @StudyWithLeandrinho refer youtube channel.\n"
        "- Pose modified: expressive hands, smiling, talking vibe.\n"
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
                badge = remove_background(badge)
                return badge

    except Exception as e:
        print("⚠ Erro ao gerar variant do Leandrinho:", e)

    return base_img


# ============================================
# APLICAR TÍTULO ESTILO YOUTUBE
# ============================================

def apply_title(img, title):
    draw = ImageDraw.Draw(img)

    title = title.replace("\n", " ").replace("\r", " ").strip()
    title = " ".join(title.split())

    try:
        font = ImageFont.truetype("impact.ttf", 88)
    except:
        font = ImageFont.truetype("arialbd.ttf", 88)

    try:
        tw = draw.textlength(title, font=font)
    except Exception:
        tw = len(title) * 22

    x = (img.width - tw) // 2
    y = 25

    # contorno
    for dx in range(-5, 6):
        for dy in range(-5, 6):
            draw.text((x + dx, y + dy), title, font=font, fill="black")

    draw.text((x, y), title, font=font, fill="white")

    return img


# ============================================
# ADICIONAR LEANDRINHO (HOLOGRAMA)
# ============================================

def add_leandrinho_badge(img, story_text):
    badge = generate_leandrinho_variant(story_text)

    badge_w = int(TARGET_W * BADGE_SIZE_RATIO)
    badge_h = int(badge_w * (badge.height / badge.width))
    badge = badge.resize((badge_w, badge_h), Image.LANCZOS)

    glow = Image.new("RGBA", (badge_w + 30, badge_h + 30), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse(
        [0, 0, badge_w + 30, badge_h + 30],
        fill=(0, 170, 255, 85)
    )
    glow = glow.filter(ImageFilter.GaussianBlur(15))

    pos_x = TARGET_W - badge_w - BADGE_PADDING
    pos_y = TARGET_H - badge_h - BADGE_PADDING

    img.alpha_composite(glow, (pos_x - 15, pos_y - 15))
    img.alpha_composite(badge, (pos_x, pos_y))
    return img


# ============================================
# FUNÇÃO PRINCIPAL
# ============================================

def generate_story_image_or_gif(story_text, safe_name, final_title):
    prompt = (
        "Generate a modern images, style miles morales universe 16:9 illustrated scene matching the story below. "
        "style marvel animations"
        "Do NOT include the narrator. Natural lighting, expressive characters.\n\n"
        f"{story_text}"
    )

    print("🧠 Gerando imagem principal...")
    result = try_gemini_main_image(prompt)

    if not result:
        print("⚠ Fallback → usando DEFAULT_IMAGE")
        img = Image.open(DEFAULT_IMAGE).convert("RGBA").resize((TARGET_W, TARGET_H))
    else:
        img = Image.open(io.BytesIO(result)).convert("RGBA")
        img = resize_no_distortion(img, TARGET_W, TARGET_H)

    img = apply_title(img, final_title)
    img = add_leandrinho_badge(img, story_text)

    output_path = f"outputs/images/{safe_name}.png"
    os.makedirs("outputs/images", exist_ok=True)
    img.save(output_path, "PNG")

    print("✔ Imagem gerada:", output_path)
    return output_path
