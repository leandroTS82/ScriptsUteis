import requests
import time
from pathlib import Path

# ============================================================
# CONFIGURAÇÃO
# ============================================================

# NOVO endpoint oficial (router)
API_URL = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-2-1"

PROMPT = (
    "A cinematic illustration of a futuristic teacher explaining English, "
    "soft lighting, clean background, professional digital art, high detail"
)

OUTPUT_DIR = Path("./output_images")
OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "image_test.png"

# ============================================================
# FUNÇÃO DE GERAÇÃO
# ============================================================

def generate_image(prompt: str, output_path: Path):
    print("Gerando imagem (HF Router – gratuito, sem API key)...")

    response = requests.post(
        API_URL,
        headers={
            "Accept": "image/png"
        },
        json={
            "inputs": prompt
        },
        timeout=300
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Erro na geração da imagem | Status: {response.status_code} | "
            f"Resposta: {response.text}"
        )

    output_path.write_bytes(response.content)
    print(f"Imagem gerada com sucesso: {output_path.resolve()}")


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":
    start = time.time()
    generate_image(PROMPT, OUTPUT_FILE)
    print(f"Tempo total: {time.time() - start:.2f}s")
