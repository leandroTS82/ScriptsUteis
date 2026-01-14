"""
============================================================
 Script: video_add_subtitle.py
 Autor: Leandro
 Descrição:
   - Aplica legenda fixa a vídeos individuais
   - Gera novos arquivos *_sub.mp4
============================================================
"""

import os
import subprocess

# ============================================================
# CONFIGURAÇÃO
# ============================================================

VIDEO_PATH = r"C:\Users\leand\Desktop\GijsDemonstration"

VIDEOS_WITH_SUBTITLES = [
    {
        "video": "01_CreatedTR_00m00s_to_00m18s.mp4",
        "text": "Created Theft Report"
    },
    {
        "video": "02_ChangeInZoho_00m00s_to_00m15s.mp4",
        "text": "Change status in Zoho status to Wachten op melding Tag''"
    },
    {
        "video": "03_Updated_In_TR_00m00s_to_00m16s.mp4",
        "text": "Updated data in Theft Report step to Waiting for tracker signal"
    },
    {
        "video": "04_ShowDataBAse01_00m00s_to_00m18s.mp4",
        "text": "Showing database records and the step date."
    },
    {
        "video": "04_ShowDataBAse02_00m00s_to_00m30s.mp4",
        "text": "Changing the creation date to force a status update to After 30 days Theft File closed."
    },
    {
        "video": "05_Confitmation_00m00s_to_00m27s.mp4",
        "text": "Confirming that the TR was finalized after 30 days."
    },
]

FFMPEG_BIN = "ffmpeg"

# ============================================================
# HELPERS
# ============================================================

def create_srt(srt_path: str, text: str):
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(
            "1\n"
            "00:00:00,000 --> 99:59:59,000\n"
            f"{text}\n"
        )


def burn_subtitle(video_file: str, srt_file: str, output_file: str):
    cmd = [
        FFMPEG_BIN,
        "-y",
        "-i", video_file,
        "-vf", f"subtitles='{srt_file}'",
        "-c:a", "copy",
        output_file
    ]

    subprocess.run(cmd, check=True)


# ============================================================
# MAIN
# ============================================================

def main():
    print("\n================ LEGENDANDO VÍDEOS ================\n")

    for item in VIDEOS_WITH_SUBTITLES:
        video = os.path.join(VIDEO_PATH, item["video"])
        text = item["text"]

        if not os.path.isfile(video):
            raise FileNotFoundError(video)

        base, _ = os.path.splitext(video)
        srt = base + ".srt"
        output = base + "_sub.mp4"

        print(f"Legendando: {os.path.basename(video)}")
        create_srt(srt, text)
        burn_subtitle(video, srt, output)

        os.remove(srt)

    print("\nProcesso finalizado.\n")


if __name__ == "__main__":
    main()
