import subprocess
import sys
from pathlib import Path

# ======================================================
# CONFIGURAÇÕES
# ======================================================
OUTPUT_DIR = Path("./downloads")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

NODE_PATH = r"C:\Program Files\nodejs\node.exe"

FORMAT = "bv*[protocol!=m3u8][ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b"
MERGE_FORMAT = "mp4"

# idiomas preferidos de legenda (ordem importa)
SUB_LANGS = ["en", "pt", "pt-BR"]

# ======================================================
# CORE
# ======================================================
def download_youtube(
    url: str,
    partition: bool = False,
    t_ini: int | None = None,
    t_end: int | None = None,
    custom_name: str | None = None,
    download_subs: bool = False,
):
    output_template = "%(title).200s.%(ext)s"
    if custom_name:
        output_template = f"{custom_name}.%(ext)s"

    command = [
        sys.executable, "-m", "yt_dlp",

        # 🔑 JS runtime explícito
        "--js-runtimes", f"node:{NODE_PATH}",

        # 🛡️ Evita SABR quebrado
        "--extractor-args", "youtube:player_client=android",

        # 🎥 Vídeo
        "-f", FORMAT,
        "--merge-output-format", MERGE_FORMAT,

        # 🧹 Estabilidade
        "--no-playlist",
        "--force-overwrites",
        "--no-part",

        # 📝 Output
        "-o", str(OUTPUT_DIR / output_template),
    ]

    # ==============================
    # 📄 Legendas (opcional)
    # ==============================
    if download_subs:
        command.extend([
            "--write-subs",                 # tenta legenda manual
            "--write-auto-subs",            # fallback automática
            "--sub-langs", ",".join(SUB_LANGS),
            "--sub-format", "srt",
            "--convert-subs", "srt",
        ])

    # ==============================
    # ✂️ Corte do vídeo
    # ==============================
    if partition and t_ini is not None and t_end is not None:
        command.extend([
            "--download-sections",
            f"*{t_ini}-{t_end}"
        ])

    command.append(url)

    print("==============================================")
    print("▶ Iniciando download do YouTube")
    print(f"▶ URL: {url}")
    if partition:
        print(f"▶ Trecho: {t_ini}s → {t_end}s")
    if download_subs:
        print(f"▶ Legendas: {', '.join(SUB_LANGS)} (manual > auto)")
    print(f"▶ Saída: {OUTPUT_DIR.resolve()}")
    print("==============================================")

    subprocess.run(command, check=True)

    print("==============================================")
    print("✔ Download concluído com sucesso")
    print("==============================================")

# ======================================================
# MAIN
# ======================================================
if __name__ == "__main__":
    url = input("Informe a URL do YouTube: ").strip()

    if not url.startswith("http"):
        print("❌ URL inválida.")
        sys.exit(1)

    partition = input("Deseja particionar? (s/n): ").strip().lower() == "s"

    t_ini = t_end = None
    if partition:
        try:
            t_ini = int(input("t_ini (em segundos): ").strip())
            t_end = int(input("t_end (em segundos): ").strip())
            if t_end <= t_ini:
                raise ValueError
        except ValueError:
            print("❌ Tempos inválidos.")
            sys.exit(1)

    custom_name = None
    if input("Deseja nomear o arquivo? (s/n): ").strip().lower() == "s":
        custom_name = input("Informe o nome do arquivo: ").strip()
        if not custom_name:
            print("❌ Nome inválido.")
            sys.exit(1)

    download_subs = input("Deseja baixar a legenda? (s/n): ").strip().lower() == "s"

    download_youtube(
        url=url,
        partition=partition,
        t_ini=t_ini,
        t_end=t_end,
        custom_name=custom_name,
        download_subs=download_subs
    )
