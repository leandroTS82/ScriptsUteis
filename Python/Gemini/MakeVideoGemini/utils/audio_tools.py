from pydub import AudioSegment

def load_audio(path: str) -> AudioSegment:
    """Carrega um arquivo de áudio (wav, mp3, etc)."""
    return AudioSegment.from_file(path)

def save_audio(audio: AudioSegment, path: str):
    """Salva áudio em WAV por padrão."""
    audio.export(path, format="wav")

def combine_audios(audio_paths: list) -> AudioSegment:
    """
    Junta vários audios em sequência.
    audio_paths: lista de caminhos de áudio.
    """
    final = AudioSegment.silent(duration=100)

    for p in audio_paths:
        segment = load_audio(p)
        final += segment

    return final

def change_volume(audio: AudioSegment, db: float) -> AudioSegment:
    """Ajusta volume (positivo aumenta, negativo reduz)."""
    return audio + db

def fade_in_out(audio: AudioSegment, fi=200, fo=200) -> AudioSegment:
    """Aplica fade in/out."""
    return audio.fade_in(fi).fade_out(fo)
