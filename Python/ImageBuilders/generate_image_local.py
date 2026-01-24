from diffusers import StableDiffusionPipeline
import torch
from pathlib import Path

# ============================================================
# CONFIG
# ============================================================

MODEL_ID = "stabilityai/stable-diffusion-2-1"
OUTPUT_DIR = Path("./output_images")
OUTPUT_DIR.mkdir(exist_ok=True)

PROMPT = (
    "A cinematic illustration of a futuristic teacher explaining English, "
    "soft lighting, clean background, professional digital art, high detail"
)

# ============================================================
# LOAD MODEL (CPU)
# ============================================================

print("Carregando modelo (primeira vez demora)...")

pipe = StableDiffusionPipeline.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.float32
)
pipe = pipe.to("cpu")

# ============================================================
# GENERATE
# ============================================================

image = pipe(
    PROMPT,
    num_inference_steps=30,
    guidance_scale=7.5
).images[0]

output_file = OUTPUT_DIR / "image_local.png"
image.save(output_file)

print(f"Imagem gerada: {output_file.resolve()}")
