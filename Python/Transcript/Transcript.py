"""
===============================================================
 Script: Extrair áudio de vídeo e gerar transcrição/tradução
 Autor: Leandro (versão aprimorada)
===============================================================

📌 O que este script faz?
---------------------------------------------------------------
Automatiza a extração de áudio, transcrição e tradução de um ou vários vídeos,
organizando tudo em pastas individuais por arquivo.

Fluxo:
1. Localiza vídeos (.mp4 ou .mkv) em um diretório especificado.
   - Pode ser passado via linha de comando: 
       python transcript.py "C:/Videos"
   - Ou definido diretamente na variável DEFAULT_VIDEO_PATH.
2. Para cada vídeo encontrado:
   - Cria uma pasta com o mesmo nome do arquivo.
   - Move o vídeo para dentro dessa pasta.
   - Extrai o áudio (.mp3) com FFmpeg.
   - Transcreve o áudio (Português e tradução para Inglês).
   - Gera saídas TXT, SRT e VTT em ./transcripts.
3. Mantém cada projeto isolado e organizado.

---------------------------------------------------------------
⚙️ Requisitos
---------------------------------------------------------------
- Python 3.9+
- Dependências Python:
    pip install torch openai-whisper
- FFmpeg instalado:
    Windows:
        winget install Gyan.FFmpeg
    Linux:
        sudo apt install ffmpeg
    macOS:
        brew install ffmpeg

---------------------------------------------------------------
📂 Estrutura de pastas resultante
---------------------------------------------------------------
Para cada vídeo processado:
📁 ./Videos/
    └── aula/
        ├── aula.mp4
        ├── mp3/
        │   └── aula.mp3
        └── transcripts/
            ├── aula.pt.txt
            ├── aula.pt.srt
            ├── aula.pt.vtt
            ├── aula.en.txt
            ├── aula.en.srt
            └── aula.en.vtt

---------------------------------------------------------------
▶️ Como executar
---------------------------------------------------------------
1. Caminho padrão (definido no código)
    python transcript.py

2. Caminho manual:
    python transcript.py "C:/MeusVideos"
    python transcript.py "C:\\Users\\leand\\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\\LTS SP Site - AliancaAmerica\\Movies"
    python transcript.py "C:\\Users\\leand\\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\\Communication site - ReunioesGravadas"

3. Caminho + arquivo específico:
    python transcript.py "C:/MeusVideos/aula01.mp4"

---------------------------------------------------------------
💡 Casos de uso
---------------------------------------------------------------
- Geração automática de legendas multilíngues.
- Transcrição de reuniões, aulas e entrevistas.
- Organização de datasets de áudio e texto.
===============================================================
"""

import whisper
import os
import glob
import subprocess
import time
import sys
import shutil
from datetime import datetime, timedelta


# ===============================================================
# ⚙️ CONFIGURAÇÃO PADRÃO
# ===============================================================
DEFAULT_VIDEO_PATH = "C:\\Users\\leand\\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\\LTS SP Site - AliancaAmerica\\Movies\\20251029.mp4"
  # Caminho padrão caso não seja passado via comando


# ===============================================================
# 🧩 FUNÇÕES AUXILIARES
# ===============================================================

def format_time_srt(secs: float) -> str:
    h = int(secs // 3600)
    m = int((secs % 3600) // 60)
    s = int(secs % 60)
    ms = int((secs % 1) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def format_time_vtt(secs: float) -> str:
    h = int(secs // 3600)
    m = int((secs % 3600) // 60)
    s = int(secs % 60)
    ms = int((secs % 1) * 1000)
    return f"{h:02}:{m:02}:{s:02}.{ms:03}"


def save_txt(segments, file_path: str):
    with open(file_path, "w", encoding="utf-8") as f:
        for seg in segments:
            f.write(seg["text"].strip() + " ")


def save_srt(segments, file_path: str):
    with open(file_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, start=1):
            f.write(f"{i}\n")
            f.write(f"{format_time_srt(seg['start'])} --> {format_time_srt(seg['end'])}\n")
            f.write(f"{seg['text'].strip()}\n\n")


def save_vtt(segments, file_path: str):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        for seg in segments:
            f.write(f"{format_time_vtt(seg['start'])} --> {format_time_vtt(seg['end'])}\n")
            f.write(f"{seg['text'].strip()}\n\n")


def extract_audio(video_path: str, output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    audio_path = os.path.join(output_dir, f"{base_name}.mp3")

    command = [
        "ffmpeg",
        "-i", video_path,
        "-map", "0:a:0",
        "-vn",
        "-acodec", "libmp3lame",
        "-q:a", "0",
        audio_path,
        "-y"
    ]

    subprocess.run(command, check=True)
    print(f"Áudio extraído: {audio_path}")
    return audio_path


def transcribe_and_translate(file_path: str, output_dir: str):
    model = whisper.load_model("medium")
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    os.makedirs(output_dir, exist_ok=True)

    # Transcrição em português
    print("Transcrevendo (Português)...")
    result_pt = model.transcribe(file_path, task="transcribe", language="pt")
    save_txt(result_pt["segments"], os.path.join(output_dir, f"{base_name}.pt.txt"))
    save_srt(result_pt["segments"], os.path.join(output_dir, f"{base_name}.pt.srt"))
    save_vtt(result_pt["segments"], os.path.join(output_dir, f"{base_name}.pt.vtt"))

    # Tradução para inglês
    print("Traduzindo (Inglês)...")
    result_en = model.transcribe(file_path, task="translate")
    save_txt(result_en["segments"], os.path.join(output_dir, f"{base_name}.en.txt"))
    save_srt(result_en["segments"], os.path.join(output_dir, f"{base_name}.en.srt"))
    save_vtt(result_en["segments"], os.path.join(output_dir, f"{base_name}.en.vtt"))

    print(f"Arquivos gerados em: {output_dir}")


def process_video(video_file: str):
    base_name = os.path.splitext(os.path.basename(video_file))[0]
    video_dir = os.path.join(os.path.dirname(video_file), base_name)

    # Cria pasta específica para o vídeo
    os.makedirs(video_dir, exist_ok=True)

    # Move vídeo para dentro da nova pasta
    new_video_path = os.path.join(video_dir, os.path.basename(video_file))
    if os.path.abspath(video_file) != os.path.abspath(new_video_path):
        shutil.move(video_file, new_video_path)

    print(f"\n🎬 Processando: {base_name}")
    print(f"Pasta criada: {video_dir}")

    # Extrai áudio
    mp3_dir = os.path.join(video_dir, "mp3")
    audio_file = extract_audio(new_video_path, mp3_dir)

    # Transcreve e traduz
    transcript_dir = os.path.join(video_dir, "transcripts")
    transcribe_and_translate(audio_file, transcript_dir)


# ===============================================================
# 🚀 EXECUÇÃO PRINCIPAL
# ===============================================================

if __name__ == "__main__":
    start_time = time.time()
    start_dt = datetime.now()

    print("\n===================================================")
    print("▶️ Iniciando processamento...")
    print(f"⏱️ Início: {start_dt.strftime('%d/%m/%Y %H:%M:%S')}")
    print("===================================================\n")

    # Caminho informado via comando
    input_arg = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_VIDEO_PATH

    # Se for um arquivo
    if os.path.isfile(input_arg):
        files_to_process = [input_arg]
    else:
        # Lista todos os vídeos no diretório
        files_to_process = glob.glob(os.path.join(input_arg, "*.mp4")) + glob.glob(os.path.join(input_arg, "*.mkv"))

    if not files_to_process:
        print(f"Nenhum vídeo encontrado em {input_arg}")
        exit(1)

    for video in files_to_process:
        try:
            process_video(video)
        except Exception as e:
            print(f"❌ Erro ao processar {video}: {e}")

    end_time = time.time()
    end_dt = datetime.now()
    elapsed = timedelta(seconds=end_time - start_time)

    print("\n===================================================")
    print("✅ Processamento concluído com sucesso!")
    print(f"⏱️ Início: {start_dt.strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"⏹️ Fim:    {end_dt.strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"⏱️ Total:  {elapsed}")
    print("===================================================\n")
