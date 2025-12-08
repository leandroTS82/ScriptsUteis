import os
import io
from PIL import Image, ImageDraw, ImageFont
from google import genai
from google.genai import types

# --------------------------------------------------------
# CONFIGURAÇÕES
# --------------------------------------------------------

DEFAULT_IMAGE = r"C:\dev\scripts\ScriptsUteis\Python\Gemini\MakeVideoGemini\assets\default_bg.png"  # usado como base para o estilo
GEMINI_KEY = r"C:\dev\scripts\ScriptsUteis\Python\Gemini\MakeVideoGemini\google-gemini-key.txt"

IMAGE_WIDTH = 1344
IMAGE_HEIGHT = 768

HEADER_HEIGHT = 110
FOOTER_HEIGHT = 120
HEADER_BG = (0, 0, 0, 160)
FOOTER_BG = (0, 0, 0, 160)

HEADER_TEXT_COLOR = "white"
FOOTER_TEXT_COLOR = "white"

HEADER_FONT_SIZE = 54
FOOTER_FONT_SIZE = 42


# --------------------------------------------------------
# LOAD KEY
# --------------------------------------------------------
def _load_key(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Chave não encontrada: {path}")
    return open(path, "r").read().strip()


# --------------------------------------------------------
# GEMINI IMAGE GENERATION
# --------------------------------------------------------
def try_gemini_image(prompt, reference_img):
    """
    Usa o modelo correto para gerar imagem:
    gemini-2.5-flash-image (gera imagens 16:9 com baixo custo)
    """
    try:
        api_key = _load_key(GEMINI_KEY)
        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[prompt, reference_img],
            config=types.GenerateContentConfig(
                image_config=types.ImageConfig(
                    aspect_ratio="16:9"
                )
            )
        )

        # SDK: retorno correto
        for part in response.candidates[0].content.parts:
            if hasattr(part, "inline_data"):
                return part.inline_data.data

        return None

    except Exception as e:
        print("⚠ Gemini image falhou:", e)
        return None


# --------------------------------------------------------
# DRAW HEADER & FOOTER
# --------------------------------------------------------
def draw_header_and_footer(final_img, title_text):
    """Adiciona header e footer com fundo escuro e texto."""
    draw = ImageDraw.Draw(final_img)

    # Fontes
    try:
        font_header = ImageFont.truetype("arial.ttf", HEADER_FONT_SIZE)
        font_footer = ImageFont.truetype("arial.ttf", FOOTER_FONT_SIZE)
    except:
        font_header = ImageFont.load_default()
        font_footer = ImageFont.load_default()

    # HEADER
    draw.rectangle(
        [0, 0, IMAGE_WIDTH, HEADER_HEIGHT],
        fill=HEADER_BG
    )

    w = draw.textlength(title_text, font=font_header)
    draw.text(
        ((IMAGE_WIDTH - w) / 2, HEADER_HEIGHT / 2 - HEADER_FONT_SIZE / 2),
        title_text,
        font=font_header,
        fill=HEADER_TEXT_COLOR
    )

    # FOOTER
    draw.rectangle(
        [0, IMAGE_HEIGHT - FOOTER_HEIGHT, IMAGE_WIDTH, IMAGE_HEIGHT],
        fill=FOOTER_BG
    )

    footer_text = "Inscreva-se no canal e deixe seu like!"
    w2 = draw.textlength(footer_text, font=font_footer)

    draw.text(
        ((IMAGE_WIDTH - w2) / 2, IMAGE_HEIGHT - FOOTER_HEIGHT + 35),
        footer_text,
        font=font_footer,
        fill=FOOTER_TEXT_COLOR
    )

    return final_img


# --------------------------------------------------------
# MAIN FUNCTION
# --------------------------------------------------------
def generate_story_image_or_gif(story_text, safe_name):
    prompt = (
        "Generate a cinematic 16:9 illustrated scene that visually represents the story below. "
        "Use soft lighting, expressive characters, emotional storytelling, and modern composition. "
        "Keep it realistic but artistic.\n\n"
        f"Story:\n{story_text}"
    )

    # Carregar imagem base do Leandrinho
    if not os.path.exists(DEFAULT_IMAGE):
        raise FileNotFoundError("DEFAULT_IMAGE não encontrada: " + DEFAULT_IMAGE)

    base_img = Image.open(DEFAULT_IMAGE)

    print("🧠 Tentando gerar imagem com Gemini...")

    result = try_gemini_image(prompt, base_img)

    # Fallback se falhar
    if not result:
        print("⚠ Falha geral na geração → usando imagem padrão.")
        final_img = base_img.resize((IMAGE_WIDTH, IMAGE_HEIGHT))
    else:
        final_img = Image.open(io.BytesIO(result))
        final_img = final_img.resize((IMAGE_WIDTH, IMAGE_HEIGHT))

    # Adicionar Header e Footer
    title_text = "História: " + safe_name.replace("_", " ").title()
    final_img = draw_header_and_footer(final_img, title_text)

    # Salvar resultado final
    output_path = f"outputs/images/{safe_name}.png"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    final_img.save(output_path, "PNG")

    print("✔ Imagem gerada e salva em:", output_path)
    return output_path
