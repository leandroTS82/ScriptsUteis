from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont


def create_text_image(text, width=1200, height=200, font_size=72):
    """
    Gera uma imagem PNG com texto usando Pillow (sem ImageMagick).
    """
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))  # Transparente
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()

    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_w = text_bbox[2] - text_bbox[0]
    text_h = text_bbox[3] - text_bbox[1]

    pos_x = (width - text_w) // 2
    pos_y = (height - text_h) // 2

    draw.text((pos_x, pos_y), text, font=font, fill="white")

    return img


def build_video(word, images_dir, audio_dir, output_path):
    audio_path = f"{audio_dir}/{word}.wav"
    img_path = f"{images_dir}/{word}.png"

    narration = AudioFileClip(audio_path)

    # Fundo principal
    bg = ImageClip(img_path).set_duration(narration.duration)

    # Caixa preta translúcida
    subtitle_bg = ColorClip(
        size=(1280, 200),
        color=(0, 0, 0)
    ).set_opacity(0.45).set_position(("center", "bottom")).set_duration(narration.duration)

    # Criar a imagem do texto
    txt_img = create_text_image(word, width=1200, height=200, font_size=70)
    txt_img_path = f"{images_dir}/{word}_subtitle.png"
    txt_img.save(txt_img_path)

    # Clip do texto
    subtitle_text = ImageClip(txt_img_path).set_position(("center", "bottom")).set_duration(narration.duration)

    # Montar vídeo final
    final = CompositeVideoClip([bg, subtitle_bg, subtitle_text]).set_audio(narration)

    final.write_videofile(
        output_path,
        fps=30,
        codec="libx264",
        audio_codec="aac"
    )
