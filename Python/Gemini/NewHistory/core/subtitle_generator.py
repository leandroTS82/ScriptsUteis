import whisper
import os
from utils.time_format import format_srt_time

_model = None

def generate_srt(audio_path: str, output_srt: str) -> None:
    global _model

    if _model is None:
        _model = whisper.load_model("base")

    result = _model.transcribe(
        audio_path,
        task="transcribe",
        language="en"
    )

    os.makedirs(os.path.dirname(output_srt), exist_ok=True)

    with open(output_srt, "w", encoding="utf-8") as f:
        for i, seg in enumerate(result["segments"], start=1):
            start = format_srt_time(seg["start"])
            end = format_srt_time(seg["end"])
            text = seg["text"].strip()

            f.write(f"{i}\n")
            f.write(f"{start} --> {end}\n")
            f.write(f"{text}\n\n")
