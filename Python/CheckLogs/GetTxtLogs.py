import subprocess
from datetime import datetime
from pathlib import Path

# =========================
# CONFIG
# =========================
NAMESPACE = "my-theft"

DEPLOYMENTS = [
    "allsetraplatform-be-eventhandlers",
    "allsetraplatform-be-handlers",
    "allsetraplatform-be-servicebushandlers",
]

TAIL_LINES = 2000  # quantidade de linhas por log

SCRIPT_NAME = Path(__file__).stem
# =========================
# PATH BASE
# =========================
BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "files" / "logs" / SCRIPT_NAME/ datetime.now().strftime("%y%m%d%H%M")
LOG_DIR.mkdir(parents=True, exist_ok=True)


# =========================
# UTILS
# =========================
def generate_filename(deployment: str) -> str:
    timestamp = datetime.now().strftime("%y%m%d%H%M")
    return f"{deployment}_{timestamp}.txt"


def run_kubectl_logs(deployment: str, tail: int = TAIL_LINES) -> str:
    try:
        result = subprocess.run(
            [
                "kubectl",
                "logs",
                f"deployment/{deployment}",
                "-n",
                NAMESPACE,
                f"--tail={tail}"
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )

        if result.returncode != 0:
            return f"[ERROR] kubectl failed:\n{result.stderr}"

        return result.stdout

    except Exception as ex:
        return f"[EXCEPTION] {str(ex)}"


def save_log(content: str, filename: str):
    file_path = LOG_DIR / filename
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return file_path


# =========================
# MAIN
# =========================
def main():
    print(f"\n📦 Namespace: {NAMESPACE}")
    print(f"📁 Output dir: {LOG_DIR}\n")

    for deployment in DEPLOYMENTS:
        print(f"🔎 Coletando logs: {deployment}")

        logs = run_kubectl_logs(deployment)

        filename = generate_filename(deployment)
        path = save_log(logs, filename)

        print(f"✅ Salvo em: {path}\n")

    print("🚀 Coleta finalizada.\n")


if __name__ == "__main__":
    main()