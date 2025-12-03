import os
import json
import subprocess
import sys
import shutil
from datetime import datetime

# -------------------------------------------------------------
# CONFIGURAÇÕES
# -------------------------------------------------------------

BATCH_FILE = r"C:\dev\scripts\ScriptsUteis\Python\ContentFabric\1GroqIA_WordBank\2ContentToCreate\CreateLater.json"

MAIN_SCRIPT = "main.py"

VIDEOS_PATH = r"C:\dev\scripts\ScriptsUteis\Python\Gemini\MakeVideoGemini\outputs\videos"

GROQ_SCRIPT = r"C:\dev\scripts\ScriptsUteis\Python\ContentFabric\4GroqIA\groq_MakeVideo.py"

UPLOAD_SCRIPT = r"C:\dev\scripts\ScriptsUteis\Python\ContentFabric\5youtube-upload\upload_youtube.py"


# -------------------------------------------------------------
# FUNÇÕES
# -------------------------------------------------------------


def load_pending():
    if not os.path.exists(BATCH_FILE):
        print("❌ O arquivo CreateLater.json não existe!")
        return []

    with open(BATCH_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get("pending", [])


def save_pending(pending_list):
    with open(BATCH_FILE, "w", encoding="utf-8") as f:
        json.dump({"pending": pending_list}, f, indent=2, ensure_ascii=False)


def run_python_script(script_path, args=None):
    """
    Executa um script Python externo aguardando a conclusão.
    Saída exibida em tempo real.
    """
    cmd = [sys.executable, script_path]

    if args:
        if isinstance(args, list):
            cmd.extend(args)
        else:
            cmd.append(args)

    print("\n🟨 Executando:", " ".join(cmd))

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    process = subprocess.Popen(
        cmd,
        stdout=sys.stdout,
        stderr=sys.stderr,
        stdin=subprocess.PIPE,
        env=env
    )
    process.communicate()

    return process.returncode == 0


# -------------------------------------------------------------
# NOVA FUNÇÃO — mover arquivos após upload
# -------------------------------------------------------------
def move_uploaded_files():
    """
    Procura arquivos com padrão:
        uploaded_YYYYMMDD_nomeDoArquivo.mp4

    Extrai "nomeDoArquivo" e move TODOS os arquivos que contenham
    este nome para a pasta:

        outputs/uploaded_YYYYMMDD
    """

    today = datetime.now().strftime("%Y%m%d")
    target_dir = fr"C:\dev\scripts\ScriptsUteis\Python\Gemini\MakeVideoGemini\outputs\uploaded_{today}"

    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        print(f"📁 Diretório criado: {target_dir}")

    print("\n📦 Procurando arquivos uploaded_...\n")

    moved_any = False

    for file in os.listdir(VIDEOS_PATH):
        if not file.startswith("uploaded_"):
            continue

        # uploaded_20251203_feeds_him.mp4
        parts = file.split("_", 2)
        if len(parts) < 3:
            continue

        base_filename = parts[2]                   # feeds_him.mp4
        base_name_without_ext = os.path.splitext(base_filename)[0]  # feeds_him

        print(f"🔍 Encontrado arquivo publicado: {file}")
        print(f"➡ Nome-base extraído: {base_name_without_ext}")

        # agora mover tudo que contenha esse nome
        for related in os.listdir(VIDEOS_PATH):
            if base_name_without_ext in related:
                src = os.path.join(VIDEOS_PATH, related)
                dst = os.path.join(target_dir, related)

                shutil.move(src, dst)
                print(f"✔ Movido: {related}")
                moved_any = True

    if not moved_any:
        print("ℹ Nenhum arquivo uploaded_ encontrado para mover.")
    else:
        print("\n🎉 Todos os arquivos relacionados foram movidos com sucesso!")


# -------------------------------------------------------------
# EXECUÇÃO PRINCIPAL
# -------------------------------------------------------------
def run_batch():

    print("\n🟦 Lendo CreateLater.json...\n")

    pending = load_pending()
    if not pending:
        print("🎉 Nada para processar!")
        return

    print(f"🟦 {len(pending)} itens encontrados na lista.\n")

    still_pending = []

    # -------------------------------------------------------------
    # ETAPA 1 — gerar vídeos com main.py
    # -------------------------------------------------------------
    for word in pending:

        print(f"\n🟦 Iniciando geração para: {word}")
        print("⏳ Aguarde...\n")

        ok = run_python_script(MAIN_SCRIPT, word)

        if ok:
            print(f"\n🟦 ✔ Concluído: {word}")
        else:
            print(f"\n⛔ Erro ao processar: {word}")
            still_pending.append(word)
            print("➡ Execução interrompida. Item mantido no pending.\n")
            save_pending(still_pending)
            return

    # tudo ok
    save_pending([])

    print("\n🟩 Todos os vídeos foram gerados! Agora vamos publicar...\n")

    # -------------------------------------------------------------
    # ETAPA 2 — groq_MakeVideo.py → gerar metadata
    # -------------------------------------------------------------
    print("🔵 Executando etapa Groq IA...")
    ok = run_python_script(GROQ_SCRIPT, VIDEOS_PATH)

    if not ok:
        print("❌ Erro na etapa Groq IA. Upload não será executado.")
        return

    print("\n🟢 Metadados criados com sucesso!\n")

    # -------------------------------------------------------------
    # ETAPA 3 — upload YouTube
    # -------------------------------------------------------------
    print("🔴 Iniciando upload para YouTube...")
    ok = run_python_script(UPLOAD_SCRIPT, VIDEOS_PATH)

    if not ok:
        print("❌ Erro ao enviar para o YouTube.")
        return

    print("\n🎉🎉 PUBLICAÇÃO COMPLETA COM SUCESSO! 🎉🎉")

    # -------------------------------------------------------------
    # ETAPA 4 — mover arquivos publicados
    # -------------------------------------------------------------
    print("\n📦 Movendo arquivos publicados...")
    move_uploaded_files()


# -------------------------------------------------------------
# MAIN
# -------------------------------------------------------------
if __name__ == "__main__":
    run_batch()
