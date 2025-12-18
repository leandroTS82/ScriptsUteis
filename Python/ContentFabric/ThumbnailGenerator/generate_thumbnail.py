from PIL import Image, ImageDraw, ImageFont
import os

def generate_thumbnail(
    image_path,
    output_path,
    title,
    highlight,
    font_path,
    text_color="#FFFFFF",
    highlight_color="#FFD700",
    stroke_color="#000000"
):
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Imagem não encontrada: {image_path}")

    if not os.path.exists(font_path):
        raise FileNotFoundError(f"Fonte não encontrada: {font_path}")

    img = Image.open(image_path).convert("RGBA")
    draw = ImageDraw.Draw(img)

    W, H = img.size

    title_font = ImageFont.truetype(font_path, size=int(H * 0.10))
    highlight_font = ImageFont.truetype(font_path, size=int(H * 0.14))

    title_y = int(H * 0.15)
    highlight_y = int(H * 0.30)

    def draw_top_left(text, y, font, fill):
        if not text:
            return

        x = int(W * 0.05)  # margem esquerda
        draw.text(
            (x, y),
            text.upper(),
            font=font,
            fill=fill,
            stroke_width=4,
            stroke_fill=stroke_color
        )

    draw_top_left(title, int(H * 0.08), title_font, text_color)
    draw_top_left(highlight, int(H * 0.20), highlight_font, highlight_color)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path)

    return output_path
