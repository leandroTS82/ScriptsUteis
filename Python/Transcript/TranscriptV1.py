"""
===============================================================
 Script: Extrair áudio de vídeo e gerar transcrição/tradução
 Autor: Leandro
===============================================================

📌 O que este script faz?
---------------------------------------------------------------
Este script automatiza o processo de gerar legendas e transcrições multilíngues a partir de vídeos.

Fluxo:
1. Busca um vídeo (formato .mp4 ou .mkv) na pasta ./movieInput/
   (ou usa um caminho definido manualmente).
2. Extrai o áudio do vídeo, convertendo para .mp3 com FFmpeg.
3. Transcreve o áudio para Português usando Whisper.
4. Traduz automaticamente a transcrição para Inglês.
5. Gera arquivos de saída em três formatos:
   - Texto contínuo (.txt)
   - Legenda SRT (.srt)
   - Legenda VTT (.vtt)

---------------------------------------------------------------
⚙️ Requisitos
---------------------------------------------------------------
- Python 3.9+
- Dependências Python:
    pip install torch openai-whisper
- FFmpeg instalado:
    Windows:
        winget install Gyan.FFmpeg
        # ou choco install ffmpeg
    Linux (Ubuntu/Debian):
        sudo apt install ffmpeg
    macOS (Homebrew):
        brew install ffmpeg

---------------------------------------------------------------
📂 Estrutura de pastas
---------------------------------------------------------------
- ./movieInput/   → coloque aqui o vídeo de entrada (.mp4 ou .mkv)
- ./mp3/          → áudio extraído (.mp3)
- ./transcripts/  → transcrições e legendas finais

---------------------------------------------------------------
▶️ Como executar
---------------------------------------------------------------
1. Coloque o vídeo em ./movieInput/
   (ou defina manualmente a variável VIDEO_FILE no script).
2. Execute:
    python transcript.py
3. Verifique as saídas na pasta ./transcripts/

---------------------------------------------------------------
📂 Saídas esperadas
---------------------------------------------------------------
Para um vídeo chamado aula.mp4, serão criados:

- aula.pt.txt   → transcrição em português
- aula.pt.srt   → legendas PT em SRT
- aula.pt.vtt   → legendas PT em VTT
- aula.en.txt   → tradução em inglês
- aula.en.srt   → legendas EN em SRT
- aula.en.vtt   → legendas EN em VTT

---------------------------------------------------------------
💡 Casos de uso
---------------------------------------------------------------
- Produção de legendas automáticas para vídeos (aulas, entrevistas, treinamentos).
- Acessibilidade: inclusão de legendas multilíngues em vídeos corporativos.
- Tradução rápida de conteúdo audiovisual.
- Preparação de datasets de legendas para IA/NLP.
- Exportação de insights de reuniões e eventos gravados.

===============================================================
"""

import whisper
import os
import glob
import subprocess
import time
from datetime import datetime, timedelta


def format_time_srt(secs: float) -> str:
    """Formata tempo para SRT (hh:mm:ss,ms)"""
    h = int(secs // 3600)
    m = int((secs % 3600) // 60)
    s = int(secs % 60)
    ms = int((secs % 1) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def format_time_vtt(secs: float) -> str:
    """Formata tempo para VTT (hh:mm:ss.ms)"""
    h = int(secs // 3600)
    m = int((secs % 3600) // 60)
    s = int(secs % 60)
    ms = int((secs % 1) * 1000)
    return f"{h:02}:{m:02}:{s:02}.{ms:03}"


def save_txt(segments, file_path: str):
    """Salva a transcrição como texto contínuo"""
    with open(file_path, "w", encoding="utf-8") as f:
        for seg in segments:
            f.write(seg["text"].strip() + " ")


def save_srt(segments, file_path: str):
    """Salva a transcrição no formato SRT"""
    with open(file_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, start=1):
            f.write(f"{i}\n")
            f.write(f"{format_time_srt(seg['start'])} --> {format_time_srt(seg['end'])}\n")
            f.write(f"{seg['text'].strip()}\n\n")


def save_vtt(segments, file_path: str):
    """Salva a transcrição no formato VTT"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        for seg in segments:
            f.write(f"{format_time_vtt(seg['start'])} --> {format_time_vtt(seg['end'])}\n")
            f.write(f"{seg['text'].strip()}\n\n")


def extract_audio(video_path: str, output_dir: str = "./mp3") -> str:
    """Extrai o primeiro stream de áudio de um vídeo (MP4/MKV) e salva como MP3"""
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    audio_path = os.path.join(output_dir, f"{base_name}.mp3")

    command = [
        "ffmpeg",
        "-i", video_path,
        "-map", "0:a:0",   # pega apenas o primeiro stream de áudio
        "-vn",             # ignora o vídeo
        "-acodec", "libmp3lame",
        "-q:a", "0",
        audio_path,
        "-y"  # sobrescreve se já existir
    ]

    subprocess.run(command, check=True)
    print(f"Áudio extraído: {audio_path}")
    return audio_path


def transcribe_and_translate(file_path: str, output_dir: str = "./transcripts"):
    """Transcreve áudio para PT e traduz para EN, salvando TXT, SRT e VTT"""
    model = whisper.load_model("medium")

    base_name = os.path.splitext(os.path.basename(file_path))[0]
    os.makedirs(output_dir, exist_ok=True)

    # 1. Transcrição em português
    result_pt = model.transcribe(file_path, task="transcribe", language="pt")
    save_txt(result_pt["segments"], os.path.join(output_dir, f"{base_name}.pt.txt"))
    save_srt(result_pt["segments"], os.path.join(output_dir, f"{base_name}.pt.srt"))
    save_vtt(result_pt["segments"], os.path.join(output_dir, f"{base_name}.pt.vtt"))

    # 2. Tradução para inglês
    result_en = model.transcribe(file_path, task="translate")
    save_txt(result_en["segments"], os.path.join(output_dir, f"{base_name}.en.txt"))
    save_srt(result_en["segments"], os.path.join(output_dir, f"{base_name}.en.srt"))
    save_vtt(result_en["segments"], os.path.join(output_dir, f"{base_name}.en.vtt"))

    print(f"Arquivos gerados em {output_dir} para {base_name}")


if __name__ == "__main__":
    # Marca início
    start_time = time.time()
    start_dt = datetime.now()
    print("\n===================================================")
    print("▶️ Iniciando processamento...")
    print(f"⏱️ Início: {start_dt.strftime('%d/%m/%Y %H:%M:%S')}")
    print("===================================================\n")

    # 🔹 Variável para indicar o vídeo manualmente
    VIDEO_FILE = ""

    if VIDEO_FILE and os.path.isfile(VIDEO_FILE):
        video_file = VIDEO_FILE
    else:
        # Se não definido, pega o primeiro vídeo em ./movieInput/
        movie_files = glob.glob("./movieInput/*.[mM][pP]4") + glob.glob("./movieInput/*.[mM][kK][vV]")

        if not movie_files:
            print("Nenhum arquivo .mp4 ou .mkv encontrado em ./movieInput/")
            exit(1)
        video_file = movie_files[0]

    print(f"Processando vídeo: {video_file}")

    # 1. Extrai áudio
    audio_file = extract_audio(video_file)

    # 2. Transcreve e traduz
    transcribe_and_translate(audio_file)

    # Marca fim
    end_time = time.time()
    end_dt = datetime.now()
    elapsed = timedelta(seconds=end_time - start_time)

    print("\n===================================================")
    print("✅ Processamento concluído com sucesso!")
    print(f"⏱️ Início: {start_dt.strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"⏹️ Fim:    {end_dt.strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"⏱️ Total:  {elapsed}")
    print("📂 Verifique os arquivos na pasta ./transcripts/")
    print("===================================================\n")
