# python run_batch.py
import os
import json
import subprocess
import sys
from datetime import datetime

BATCH_DIRECTORY = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Base\TermsReadyToBeCreated"
HISTORY_FILE = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Base\history_generated.json"
# ============================================================
# PATHS DE DESTINO PARA VERIFICAR REDUNDÂNCIA
# ============================================================

VIDEO_OUTPUT_PATHS = [
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\Videos",
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\EnableToYoutubeUpload",
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\VideosSemJson",
    r"C:\Users\leand\Desktop\wordbank",
]

MAIN_SCRIPT = "main.py"

def load_history_terms():
    """
    Retorna apenas termos que foram gerados com sucesso.
    Termos com erro=True serão reprocessados.
    """
    if not os.path.exists(HISTORY_FILE):
        return set()

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)

        return {
            item.get("term")
            for item in history
            if item.get("term") and item.get("error") is False
        }

    except Exception as e:
        print(f" Erro ao ler histórico: {e}")
        return set()

def load_pending():
    """
    Lê todos os JSON do diretório BATCH_DIRECTORY,
    consolida os termos "pending",
    remove duplicados preservando ordem,
    ignora termos já existentes no HISTORY_FILE.
    """
    if not os.path.exists(BATCH_DIRECTORY):
        print(" Diretório CreateLater não existe!")
        return []

    consolidated = []

    json_files = [
        f for f in os.listdir(BATCH_DIRECTORY)
        if f.lower().endswith(".json")
    ]

    if not json_files:
        print(" Nenhum JSON encontrado no diretório.")
        return []

    # 🔥 Carrega histórico uma única vez (performance)
    history_terms = load_history_terms()

    for file in json_files:
        path = os.path.join(BATCH_DIRECTORY, file)

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            pending = data.get("pending", [])
            print(f" 📂 {file} → {len(pending)} termos")

            consolidated.extend(pending)

        except Exception as e:
            print(f" Erro ao ler {file}: {e}")

    # 🔁 Remove duplicados preservando ordem
    seen = set()
    unique_terms = []

    for term in consolidated:
        if term in seen:
            continue

        seen.add(term)

        # 🚫 Ignora se já estiver no histórico
        if term in history_terms:
            print(f" ⏭️ Ignorando '{term}' (já gerado anteriormente)")
            continue

        unique_terms.append(term)

    print(f"\n Total consolidado (novos termos): {len(unique_terms)}\n")

    return unique_terms

def register_history(term: str, success: bool, error_message: str = None):
    """
    Registra ou atualiza histórico.
    Se já existir registro, atualiza.
    """

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    history = []

    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []

    # procura registro existente
    existing = next((h for h in history if h.get("term") == term), None)

    if existing:
        if success:
            existing["error"] = False
            existing.pop("errorDetail", None)
            existing["generated_at"] = now
        else:
            existing["error"] = True
            existing["errorDetail"] = {
                "dt": now,
                "msgError": error_message
            }
    else:
        record = {
            "term": term,
            "generated_at": now,
            "error": not success
        }

        if not success:
            record["errorDetail"] = {
                "dt": now,
                "msgError": error_message
            }

        history.append(record)

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def normalize_term(term: str) -> str:
    """
    Normaliza o termo para comparação com nomes de arquivos/pastas.
    Ex: 'no matter' -> 'no_matter'
    """
    return term.strip().lower().replace(" ", "_")


VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm"}

def term_already_generated(term: str) -> bool:
    normalized = normalize_term(term)

    for base_path in VIDEO_OUTPUT_PATHS:
        if not os.path.exists(base_path):
            continue

        for root, _, files in os.walk(base_path):
            for file in files:
                name, ext = os.path.splitext(file.lower())

                if name == normalized and ext in VIDEO_EXTENSIONS:
                    print(f" 🔁 JÁ EXISTE → '{term}' encontrado em:")
                    print(f"    {os.path.join(root, file)}")
                    return True

    return False

def run_word(word):
    print("\n Iniciando geração para:", word)
    print(" Aguarde...\n")

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    try:
        process = subprocess.Popen(
            [sys.executable, MAIN_SCRIPT, word],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            env=env
        )

        full_output = []

        # 🔴 STREAM EM TEMPO REAL
        for line in process.stdout:
            print(line, end="")  # mostra imediatamente
            full_output.append(line)

        process.wait()

        if process.returncode != 0:
            return False, "".join(full_output).strip()

        return True, None

    except Exception as e:
        return False, str(e)
    
def print_progress(current, total, word):
    """
    Barra de progresso simples no console.
    """
    bar_length = 30
    progress = current / total
    filled = int(bar_length * progress)
    bar = "█" * filled + "░" * (bar_length - filled)
    percent = int(progress * 100)

    print(f"\n[{bar}] {current}/{total} ({percent}%) → {word}\n")


def run_batch():
    start_time = datetime.now()
    print("\n Início do processamento:", start_time.strftime("%H:%M:%S"))
    print("\n Lendo CreateLater.json...\n")

    pending = load_pending()
    if not pending:
        print(" Nada para processar!")

        end = datetime.now()
        print("\n Fim:", end.strftime("%H:%M:%S"))
        print("Duração:", str(end - start_time).split(".")[0])
        return

    print(f" {len(pending)} itens encontrados na lista.\n")

    still_pending = []

    total = len(pending)

    for index, word in enumerate(pending, start=1):
        # --------------------------------------------
        # VERIFICAÇÃO DE REDUNDÂNCIA (ANTI-CUSTO)
        # --------------------------------------------
        if term_already_generated(word):
            print(f" ⏭️  Pulando '{word}' (já processado anteriormente)\n")
            continue

        print_progress(index, total, word)
        success, error_msg = run_word(word)

        if success:
            print(f"Concluído: {word}")
            register_history(word, True)
        else:
            print(f" Erro ao processar: {word}")
            print(" Motivo:", error_msg)
            register_history(word, False, error_msg)
            break

    if not still_pending:
        print("\n Todos os vídeos foram gerados com sucesso!")
    else:
        print("\n PROCESSAMENTO INTERROMPIDO — ainda restam itens no pending!")

    # Hora de término
    end = datetime.now()
    print("\n Fim do processamento:", end.strftime("%H:%M:%S"))

    # Duração total formatada
    duration = str(end - start_time).split(".")[0]
    print(" Tempo total:", duration)


if __name__ == "__main__":
    run_batch()
