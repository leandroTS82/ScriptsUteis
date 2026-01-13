import subprocess
import sys
import os
from datetime import datetime

# python pipeline_makevideo_Youtube.py   

# ------------------------------
# Função auxiliar para executar scripts e aguardar finalização
# ------------------------------
def run_step(description: str, command: list):
    print("\n=======================================================")
    print(f"▶ INICIANDO: {description}")
    print("=======================================================\n")

    try:
        subprocess.run(command, check=True)
        print("\n=======================================================")
        print(f"✔ FINALIZADO: {description}")
        print("=======================================================\n")

    except subprocess.CalledProcessError as e:
        print("\n=======================================================")
        print(f"❌ ERRO ao executar: {description}")
        print(f"Comando: {command}")
        print(e)
        print("=======================================================\n")
        sys.exit(1)


# ------------------------------
# Caminhos configuráveis
# ------------------------------

PATH_CONTENT = r"C:\\dev\\scripts\\ScriptsUteis\\Python\\MakeVideo\\Content\\ToUplod"

# 1 - BatchMakeVideos.py
SCRIPT1 = r"C:\\dev\\scripts\\ScriptsUteis\\Python\\MakeVideo\\BatchMakeVideos.py"

# 2 - Groq_MakeVideo
SCRIPT2 = r"C:\\dev\\scripts\\ScriptsUteis\\Python\\GroqIA\\groq_MakeVideo.py"
OUTPUT_GROQ = r"C:\\Users\\leand\\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\\LTS SP Site - Audios para estudar inglês\\VideosGeradosPorScript\\GOOGLE_TTS\\WordBank"

# 3 - YouTube upload
SCRIPT3 = r"C:\\dev\\scripts\\ScriptsUteis\\Python\\youtube-upload\\upload_youtube.py"


# ------------------------------
# Pipeline completo
# ------------------------------
def main():

    print("\n=======================================================")
    print("🚀 INICIANDO PIPELINE COMPLETO — MAKE VIDEO -> GROQ -> UPLOAD")
    print("Data:", datetime.now())
    print("=======================================================\n")

    # 1️⃣ Etapa 1 — Gerar vídeos
    run_step(
        "GERAÇÃO DE VÍDEOS (BatchMakeVideos)",
        ["python", SCRIPT1, PATH_CONTENT]
    )

    # 2️⃣ Etapa 2 — Processamento Groq
    run_step(
        "PROCESSAMENTO GROQ (groq_MakeVideo)",
        ["python", SCRIPT2, PATH_CONTENT, OUTPUT_GROQ]
    )

    # 3️⃣ Etapa 3 — Upload YouTube
    run_step(
        "UPLOAD PARA O YOUTUBE",
        ["python", SCRIPT3, OUTPUT_GROQ]
    )

    print("\n=======================================================")
    print("  PIPELINE FINALIZADO COM SUCESSO!")
    print("=======================================================\n")


if __name__ == "__main__":
    main()
