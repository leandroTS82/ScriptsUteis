import os
import io
import base64
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
from google import genai
from google.genai import types
from groq import Groq

# ================================================================
# CONFIGURAÇÕES
# ================================================================

DEFAULT_IMAGE = r"C:\dev\scripts\ScriptsUteis\Python\Gemini\MakeVideoGemini\assets\default_bg.png"
GEMINI_KEY   = r"C:\dev\scripts\ScriptsUteis\Python\Gemini\MakeVideoGemini\google-gemini-key.txt"
GROQ_KEY     = r"C:\dev\scripts\ScriptsUteis\Python\Gemini\MakeVideoGemini\groq_api_key.txt"

TARGET_W = 1344
TARGET_H = 768

BADGE_SIZE_RATIO = 0.18
BADGE_PADDING = 30


# ================================================================
# HELPERS
# ================================================================

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


# ================================================================
# 1) TÍTULO SEO
# ================================================================

def generate_seo_title(story_text):
    prompt = f"""
Crie um título curto, chamativo, estilo thumbnail YouTube.
Máximo 48 caracteres. Sem emojis.

História:
{story_text}
"""

    try:
        client = Groq(api_key=_load_key(GROQ_KEY))
        res = client.chat.completions.create(
            model="llama-3.2-1b-preview",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=40
        )
        title = res.choices[0].message["content"].strip()
        if title:
            return title
    except:
        pass

    try:
        client = genai.Client(api_key=_load_key(GEMINI_KEY))
        res = client.models.generate_content(
            model="gemini-2.0-flash-lite-preview",
            contents=prompt
        )
        return res.text.strip()
    except:
        return "História Incrível"


# ================================================================
# 2) IMAGEM PRINCIPAL
# ================================================================

def try_gemini_image(prompt):
    try:
        client = genai.Client(api_key=_load_key(GEMINI_KEY))
        res = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=prompt,
            config=types.GenerateContentConfig(
                image_config=types.ImageConfig(aspect_ratio="16:9")
            )
        )
        for part in res.candidates[0].content.parts:
            if hasattr(part, "inline_data") and part.inline_data:
                return part.inline_data.data
    except Exception as e:
        print("⚠ Gemini image falhou:", e)

    return None


def try_groq_image(prompt):
    try:
        client = Groq(api_key=_load_key(GROQ_KEY))
        res = client.images.generate(
            model="luma-flux-schnell",
            prompt=prompt,
            size="1024x576"
        )

        if hasattr(res, "image_base64"):
            return base64.b64decode(res.image_base64)

    except Exception as e:
        print("⚠ Groq image falhou:", e)

    return None


# ================================================================
# 3) REMOVER FUNDO (SEM OPENCV)
# ================================================================

def remove_background(pil_img):
    img = pil_img.convert("RGBA")
    pixels = img.load()

    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = pixels[x, y]

            # Considera fundo branco ou claro
            if r > 200 and g > 200 and b > 200:
                pixels[x, y] = (r, g, b, 0)

    return img


# ================================================================
# 4) VARIANTE DO LEANDRINHO
# ================================================================

def generate_leandrinho_variant():
    prompt = (
        "Generate a small transparent PNG illustration of Leandrinho, the cheerful Brazilian English teacher. "
        "Keep the same identity but change pose to a happy presenter. "
        "NO BACKGROUND. Transparent only."
    )

    try:
        base_img = Image.open(DEFAULT_IMAGE).convert("RGBA")
        client = genai.Client(api_key=_load_key(GEMINI_KEY))

        res = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[prompt, base_img],
            config=types.GenerateContentConfig(
                image_config=types.ImageConfig(aspect_ratio="1:1")
            )
        )

        for part in res.candidates[0].content.parts:
            if part.inline_data:
                badge_raw = Image.open(io.BytesIO(part.inline_data.data)).convert("RGBA")
                return remove_background(badge_raw)

    except Exception as e:
        print("⚠ Falha ao gerar variante do Leandrinho:", e)

    return Image.open(DEFAULT_IMAGE).convert("RGBA")


# ================================================================
# 5) APRIMORAR SELO (sombra + borda)
# ================================================================

def enhance_badge(badge):
    shadow = Image.new("RGBA", (badge.width+20, badge.height+20), (0,0,0,0))
    sd = ImageDraw.Draw(shadow)
    sd.ellipse([10,10,badge.width+10, badge.height+10], fill=(0,0,0,120))
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))

    mask = Image.new("L", badge.size, 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.rounded_rectangle([0,0,badge.width,badge.height], radius=45, fill=255)
    badge.putalpha(mask)

    return shadow, badge


# ================================================================
# 6) TÍTULO ESTILO YOUTUBE
# ================================================================

def apply_title(img, title):
    draw = ImageDraw.Draw(img)

    # =====================================================
    # NORMALIZAÇÃO DO TEXTO (EVITA multiline)
    # =====================================================
    title = title.replace("\n", " ").replace("\r", " ").strip()
    title = " ".join(title.split())  # remove múltiplos espaços

    # =====================================================
    # FONTE ESTILO YOUTUBE
    # =====================================================
    try:
        font = ImageFont.truetype("impact.ttf", 88)
    except:
        try:
            font = ImageFont.truetype("arialbd.ttf", 88)
        except:
            font = ImageFont.load_default()

    # =====================================================
    # MEDIR TEXTO SEM ERROS
    # =====================================================
    try:
        tw = draw.textlength(title, font=font)
    except Exception:
        # fallback seguro
        tw = len(title) * 20  

    x = (img.width - tw) // 2
    y = 25

    # =====================================================
    # CONTORNO GROSSO (EFEITO YOUTUBE)
    # =====================================================
    for dx in range(-4, 5):
        for dy in range(-4, 5):
            draw.text((x + dx, y + dy), title, font=font, fill="black")

    # =====================================================
    # TEXTO FINAL
    # =====================================================
    draw.text((x, y), title, font=font, fill="white")

    return img



# ================================================================
# 7) FUNÇÃO PRINCIPAL
# ================================================================

def generate_story_image_or_gif(story_text, safe_name):
    print("🧠 Gerando título SEO...")
    title = generate_seo_title(story_text)

    prompt = (
        "Create a cinematic expressive 16:9 illustration based on the story. "
        "DO NOT include Leandrinho. Natural characters only.\n\n"
        f"{story_text}"
    )

    raw = try_gemini_image(prompt) or try_groq_image(prompt)

    if not raw:
        img = Image.open(DEFAULT_IMAGE).convert("RGBA")
        img = resize_no_distortion(img, TARGET_W, TARGET_H)
    else:
        img = Image.open(io.BytesIO(raw)).convert("RGBA")
        img = resize_no_distortion(img, TARGET_W, TARGET_H)

    # título
    img = apply_title(img, title)

    # selo
    badge = generate_leandrinho_variant()
    shadow, badge = enhance_badge(badge)

    bw = int(TARGET_W * BADGE_SIZE_RATIO)
    bh = int(bw * (badge.height / badge.width))
    badge = badge.resize((bw, bh), Image.LANCZOS)
    shadow = shadow.resize((bw+20, bh+20), Image.LANCZOS)

    px = TARGET_W - bw - BADGE_PADDING
    py = TARGET_H - bh - BADGE_PADDING

    img.alpha_composite(shadow, (px-10, py-10))
    img.alpha_composite(badge, (px, py))

    out = f"outputs/images/{safe_name}.png"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.save(out, "PNG")

    print("✔ Imagem gerada:", out)
    return out
