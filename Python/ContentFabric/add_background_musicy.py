from pathlib import Path
from random import choice
from pydub import AudioSegment

# ======================================================
# CONFIGURAÇÕES
# ======================================================

VOICE_DIR = Path(
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\NewAudios_Gemini"
)

BACKGROUND_MUSIC_DIR = Path(
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\NewAudios_Gemini\FundoMusical"
)

OUTPUT_DIR = Path(
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\NewAudios_Gemini\voz_com_fundo"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MUSIC_VOLUME_DB = -18
FADE_IN_MS = 3000
FADE_OUT_MS = 3000

SUPPORTED_EXT = (".wav", ".mp3")


# ======================================================
# FUNÇÕES
# ======================================================

def load_audio(path: Path) -> AudioSegment:
    return AudioSegment.from_file(path)


def adjust_music_length(music: AudioSegment, target_ms: int) -> AudioSegment:
    if len(music) < target_ms:
        loops = (target_ms // len(music)) + 1
        music = music * loops
    return music[:target_ms]


def mix_voice_with_music(voice: AudioSegment, music: AudioSegment) -> AudioSegment:
    music = music + MUSIC_VOLUME_DB
    music = adjust_music_length(music, len(voice))
    music = music.fade_in(FADE_IN_MS).fade_out(FADE_OUT_MS)
    return voice.overlay(music)


# ======================================================
# PROCESSAMENTO EM LOTE
# ======================================================

def process_batch():
    voices = [p for p in VOICE_DIR.iterdir() if p.suffix.lower() in SUPPORTED_EXT]
    musics = [p for p in BACKGROUND_MUSIC_DIR.iterdir() if p.suffix.lower() in SUPPORTED_EXT]

    if not voices:
        print("❌ Nenhum áudio de voz encontrado.")
        return

    if not musics:
        print("❌ Nenhuma trilha de fundo encontrada.")
        return

    print(f"🎧 Vozes encontradas: {len(voices)}")
    print(f"🎶 Trilhas disponíveis: {len(musics)}\n")

    for voice_path in voices:
        try:
            music_path = choice(musics)

            print(f"▶ Processando: {voice_path.name}")
            print(f"   🎵 Fundo: {music_path.name}")

            voice = load_audio(voice_path)
            music = load_audio(music_path)

            final_audio = mix_voice_with_music(voice, music)

            output_path = OUTPUT_DIR / voice_path.name
            final_audio.export(output_path, format="wav")

            print(f"   ✅ Gerado: {output_path}\n")

        except Exception as e:
            print(f"❌ Erro em {voice_path.name}: {e}\n")


# ======================================================
# MAIN
# ======================================================

if __name__ == "__main__":
    process_batch()
