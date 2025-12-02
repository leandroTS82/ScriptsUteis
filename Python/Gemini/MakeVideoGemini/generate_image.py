import os
import shutil

DEFAULT_IMG = "assets/default_bg.png"

def generate_image(word, output_path):
    """
    Não gera imagem via IA.
    Sempre copia a imagem padrão.
    """
    print("🖼️ Usando imagem fixa padrão...")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    shutil.copy(DEFAULT_IMG, output_path)

    print("✔ Imagem salva em:", output_path)
    return output_path
