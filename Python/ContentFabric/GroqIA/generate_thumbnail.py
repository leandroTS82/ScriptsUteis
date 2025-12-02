"""
=====================================================================
 Script: generate_thumbnail.py
 Autor: Leandro (via Gemini)
 Finalidade: Gera thumbnails .jpg automaticamente lendo metadados.
=====================================================================
"""
import os
import json
import textwrap
from PIL import Image, ImageDraw, ImageFont

# --- CONFIGURAÇÕES VISUAIS ---
TEMPLATE_WIDTH = 1280
TEMPLATE_HEIGHT = 720
BACKGROUND_COLOR = (25, 25, 112) # Azul Marinho (se não tiver imagem de fundo)
TEXT_COLOR = (255, 255, 0)       # Amarelo (Chama atenção)
STROKE_COLOR = (0, 0, 0)         # Contorno Preto
STROKE_WIDTH = 6                 # Grossura do contorno

# Caminhos (Ajuste para seu ambiente)
ASSETS_DIR = "./assets" 
FONT_PATH = os.path.join(ASSETS_DIR, "Impact.ttf") # Baixe essa fonte!
AVATAR_PATH = os.path.join(ASSETS_DIR, "Leandrinho_Apontando.png")
BG_PATH = os.path.join(ASSETS_DIR, "fundo_padrao.jpg") # Opcional

def create_thumbnail(json_path):
    # 1. Carregar Metadados
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Pega o texto curto (ou usa o título truncado se a Groq falhar)
    raw_text = data.get("thumbnail_text", data.get("title", "AULA DE INGLÊS"))
    if len(raw_text) > 25: raw_text = raw_text[:25] # Segurança
    
    # 2. Criar Base
    if os.path.exists(BG_PATH):
        img = Image.open(BG_PATH).resize((TEMPLATE_WIDTH, TEMPLATE_HEIGHT))
    else:
        img = Image.new('RGB', (TEMPLATE_WIDTH, TEMPLATE_HEIGHT), color=BACKGROUND_COLOR)
    
    draw = ImageDraw.Draw(img)
    
    # 3. Adicionar Avatar (Canto Direito)
    if os.path.exists(AVATAR_PATH):
        avatar = Image.open(AVATAR_PATH).convert("RGBA")
        # Redimensiona avatar para caber bem (ex: 80% da altura)
        scale_factor = 0.9
        target_h = int(TEMPLATE_HEIGHT * scale_factor)
        aspect_ratio = avatar.width / avatar.height
        target_w = int(target_h * aspect_ratio)
        avatar = avatar.resize((target_w, target_h), Image.Resampling.LANCZOS)
        
        # Cola na direita
        x_pos = TEMPLATE_WIDTH - target_w
        y_pos = TEMPLATE_HEIGHT - target_h
        img.paste(avatar, (x_pos, y_pos), avatar)

    # 4. Configurar Fonte e Texto
    # Tenta carregar fonte, senão usa padrão
    try:
        font_size = 130
        font = ImageFont.truetype(FONT_PATH, font_size)
    except:
        font = ImageFont.load_default()
        font_size = 40 # Fallback
        
    # Quebra de linha inteligente (Wrap)
    # Ajustamos a largura do texto para ocupar só o lado ESQUERDO (onde não tem avatar)
    max_text_width = int(TEMPLATE_WIDTH * 0.60) 
    
    # Lógica simples de quebra (reduz tamanho se não couber)
    lines = []
    while font_size > 50:
        font = ImageFont.truetype(FONT_PATH, font_size)
        # Tenta quebrar o texto para caber na largura
        avg_char_width = font.getlength("A")
        chars_per_line = int(max_text_width / avg_char_width)
        lines = textwrap.wrap(raw_text, width=chars_per_line)
        
        # Verifica se a altura total cabe
        total_height = len(lines) * font_size * 1.2
        if total_height < TEMPLATE_HEIGHT * 0.8:
            break
        font_size -= 10 # Diminui fonte e tenta de novo

    # 5. Desenhar Texto com Contorno (Stroke)
    text_y = (TEMPLATE_HEIGHT - (len(lines) * font_size)) // 2 # Centraliza Verticalmente
    
    for line in lines:
        # Calcula largura da linha para centralizar na área esquerda
        line_w = font.getlength(line)
        text_x = 50 # Margem esquerda fixa
        
        # Desenha contorno grosso (Stroke)
        # Pillow mais novo tem parâmetro stroke_width, mas esse loop garante compatibilidade e grossura
        for adj_x in range(-STROKE_WIDTH, STROKE_WIDTH+1):
            for adj_y in range(-STROKE_WIDTH, STROKE_WIDTH+1):
                draw.text((text_x+adj_x, text_y+adj_y), line, font=font, fill=STROKE_COLOR)
        
        # Desenha texto principal
        draw.text((text_x, text_y), line, font=font, fill=TEXT_COLOR)
        
        text_y += int(font_size * 1.1)

    # 6. Salvar
    # Salva com o mesmo nome do JSON, mas extensão .jpg
    output_path = json_path.replace(".json", ".jpg")
    img.save(output_path, quality=95)
    print(f"🖼️ Thumbnail gerada: {output_path}")
    return output_path

# --- Integração Rápida para Teste ---
if __name__ == "__main__":
    import sys
    # Se passar arquivo como argumento, processa
    if len(sys.argv) > 1:
        create_thumbnail(sys.argv[1])
    else:
        print("Arraste um JSON para este script para testar.")