import os, sys
from generate_script import generate_lesson_json
from generate_audio import generate_audio
from generate_image import generate_image
from generate_video import build_video

# --- Palavra via argumento ---
if len(sys.argv) < 2:
    print("❌ Informe a palavra. Exemplo:")
    print("   python main.py crowd")
    sys.exit(1)

WORD = sys.argv[1].strip().lower()
print(f"📌 Gerando vídeo para: {WORD}")

# Criar pastas
os.makedirs("outputs/audio", exist_ok=True)
os.makedirs("outputs/images", exist_ok=True)
os.makedirs("outputs/videos", exist_ok=True)

# 1) ROTEIRO
lesson = generate_lesson_json(WORD)

# 2) IMAGEM
img_path = f"outputs/images/{WORD}.png"
generate_image(WORD, img_path)

# 3) ÁUDIO
text = " ".join(b["text"] for b in lesson["WORD_BANK"][0])
audio_path = f"outputs/audio/{WORD}.wav"
generate_audio(text, audio_path)

# 4) VÍDEO FINAL
video_path = f"outputs/videos/{WORD}.mp4"
build_video(WORD, "outputs/images", "outputs/audio", video_path)

print("🎉 VÍDEO GERADO COM SUCESSO:")
print(video_path)
