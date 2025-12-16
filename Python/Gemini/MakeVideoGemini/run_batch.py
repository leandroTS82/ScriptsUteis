# python run_batch.py
import os
import json
import subprocess
import sys
from datetime import datetime

BATCH_FILE = r"C:\dev\scripts\ScriptsUteis\Python\AI_EnglishHelper\CreateLater.json"
MAIN_SCRIPT = "main.py"


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


def run_word(word):
    print("\n🟦 Iniciando geração para:", word)
    print("⏳ Aguarde...\n")

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    try:
        subprocess.run(
            [sys.executable, MAIN_SCRIPT, word],
            capture_output=False,
            text=True,
            encoding="utf-8",
            env=env
        )
        return True

    except Exception as e:
        print("❌ ERRO AO EXECUTAR main.py:")
        print(e)
        return False


def run_batch():
    start_time = datetime.now()
    print("\n🕒 Início do processamento:", start_time.strftime("%H:%M:%S"))
    print("\n🟦 Lendo CreateLater.json...\n")

    pending = load_pending()
    if not pending:
        print("🎉 Nada para processar!")

        end = datetime.now()
        print("\n🕒 Fim:", end.strftime("%H:%M:%S"))
        print("⏱ Duração:", str(end - start_time).split(".")[0])
        return

    print(f"🟦 {len(pending)} itens encontrados na lista.\n")

    still_pending = []

    for word in pending:
        ok = run_word(word)

        if ok:
            print(f"\n🟦 ✔ Concluído: {word}")
        else:
            print(f"\n⛔ Erro ao processar: {word}")
            still_pending.append(word)
            print("➡ Item mantido no pending.\n")
            break

    save_pending(still_pending)

    if not still_pending:
        print("\n🟦 🎉 Todos os vídeos foram gerados com sucesso!")
    else:
        print("\n🟦 ⚠ PROCESSAMENTO INTERROMPIDO — ainda restam itens no pending!")

    # Hora de término
    end = datetime.now()
    print("\n🕒 Fim do processamento:", end.strftime("%H:%M:%S"))

    # Duração total formatada
    duration = str(end - start_time).split(".")[0]
    print("⏱ Tempo total:", duration)


if __name__ == "__main__":
    run_batch()
