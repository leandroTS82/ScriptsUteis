import subprocess
import random
import time
from pathlib import Path

# ======================================================
# CONFIGURAÇÕES
# ======================================================

FFMPEG_PATH = r"C:\ffmpeg\bin\ffmpeg.exe"

VOICE_DIR = Path(
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\NewAudios_Gemini"
)

MUSIC_DIR = Path(
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\NewAudios_Gemini\FundoMusical"
)

OUTPUT_DIR = Path(
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\NewAudios_Gemini\voz_com_fundo"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SUPPORTED_EXT = (".wav", ".mp3")

MUSIC_VOLUME_DB = -18
FADE_IN = 3
FADE_OUT = 3

# ======================================================
# FUNÇÕES
# ======================================================

def run_ffmpeg(cmd: list):
    subprocess.run(
        cmd,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )


def mix_audio(voice_path: Path, music_path: Path, output_path: Path):
    cmd = [
        FFMPEG_PATH,
        "-y",
        "-loglevel", "error",

        "-i", str(voice_path),

        "-stream_loop", "-1",
        "-i", str(music_path),

        "-filter_complex",
        (
            f"[1:a]volume={MUSIC_VOLUME_DB}dB,"
            f"afade=t=in:st=0:d={FADE_IN},"
            f"afade=t=out:st=0:d={FADE_OUT}[bg];"
            f"[0:a][bg]amix=inputs=2"
        ),

        "-shortest",
        str(output_path)
    ]

    run_ffmpeg(cmd)


# ======================================================
# PROCESSAMENTO EM LOTE
# ======================================================

def process_batch():
    voices = [p for p in VOICE_DIR.iterdir() if p.suffix.lower() in SUPPORTED_EXT]
    musics = [p for p in MUSIC_DIR.iterdir() if p.suffix.lower() in SUPPORTED_EXT]

    total = len(voices)

    if total == 0 or not musics:
        print("❌ Nada para processar.")
        return

    print(f"\n🎧 Arquivos: {total}")
    print(f"🎶 Trilhas: {len(musics)}\n")

    for idx, voice in enumerate(voices, start=1):
        music = random.choice(musics)
        output = OUTPUT_DIR / voice.name

        print(f"[{idx}/{total}] ▶ {voice.name}")
        print(f"           🎵 Fundo: {music.name}")

        start = time.time()

        try:
            mix_audio(voice, music, output)
            elapsed = time.time() - start
            print(f"           ✅ Concluído em {elapsed:.2f}s\n")

        except subprocess.CalledProcessError as e:
            print(f"❌ Erro em {voice.name}")
            print(e.stderr)
            print()


# ======================================================
# MAIN
# ======================================================

if __name__ == "__main__":
    process_batch()
