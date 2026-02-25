import subprocess
import sys
import json
import re
from pathlib import Path
from datetime import timedelta

# ======================================================
# CONSTANTES
# ======================================================
DEFAULT_OUTPUT_DIR = Path("./downloads")
CONFIG_FILE = Path("./output_dirs.json")

NODE_PATH = r"C:\Program Files\nodejs\node.exe"

FORMAT = "bv*[protocol!=m3u8][ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b"
MAX_QUALITY_FORMAT = "bestvideo+bestaudio/best"

MERGE_FORMAT = "mp4"

PRIMARY_SUB_LANG = "en"
FALLBACK_SUB_LANG = "pt"

# ======================================================
# UTILS – TEMPO
# ======================================================
def parse_time_input(value: str) -> int:
    value = value.strip()

    if value.isdigit():
        return int(value)

    parts = value.split(":")
    if len(parts) == 2:
        m, s = parts
        return int(m) * 60 + int(s)

    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + int(s)

    raise ValueError("Formato de tempo inválido")

# ======================================================
# UTILS – SRT
# ======================================================
def parse_srt_time(t: str) -> timedelta:
    h, m, s_ms = t.split(":")
    s, ms = s_ms.split(",")
    return timedelta(
        hours=int(h),
        minutes=int(m),
        seconds=int(s),
        milliseconds=int(ms)
    )


def format_srt_time(td: timedelta) -> str:
    total_ms = int(td.total_seconds() * 1000)
    ms = total_ms % 1000
    total_s = total_ms // 1000
    s = total_s % 60
    total_m = total_s // 60
    m = total_m % 60
    h = total_m // 60
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def trim_srt(srt_path: Path, t_ini: int, t_end: int):
    start = timedelta(seconds=t_ini)
    end = timedelta(seconds=t_end)

    blocks = srt_path.read_text(encoding="utf-8").split("\n\n")
    new_blocks = []
    index = 1

    for block in blocks:
        lines = block.strip().splitlines()
        if len(lines) < 3:
            continue

        match = re.match(r"(.*) --> (.*)", lines[1])
        if not match:
            continue

        t1 = parse_srt_time(match.group(1))
        t2 = parse_srt_time(match.group(2))

        if t2 < start or t1 > end:
            continue

        t1 = max(t1, start) - start
        t2 = min(t2, end) - start

        new_blocks.append("\n".join([
            str(index),
            f"{format_srt_time(t1)} --> {format_srt_time(t2)}",
            *lines[2:]
        ]))
        index += 1

    srt_path.write_text("\n\n".join(new_blocks), encoding="utf-8")

# ======================================================
# OUTPUT DIR MANAGEMENT
# ======================================================
def load_saved_dirs():
    if not CONFIG_FILE.exists():
        return []
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f).get("paths", [])


def save_dir(path: Path):
    paths = load_saved_dirs()
    p = str(path.resolve())
    if p not in paths:
        paths.append(p)
        CONFIG_FILE.write_text(
            json.dumps({"paths": paths}, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )


def choose_output_dir() -> Path:
    print("\nEscolha o diretório de saída:")
    print("1 - Usar diretório padrão (./downloads)")
    print("2 - Informar novo diretório (salvar)")
    print("3 - Escolher diretório salvo")

    opt = input("Opção (1/2/3): ").strip()

    if opt == "1":
        DEFAULT_OUTPUT_DIR.mkdir(exist_ok=True)
        return DEFAULT_OUTPUT_DIR

    if opt == "2":
        p = Path(input("Informe o caminho completo: ").strip())
        p.mkdir(parents=True, exist_ok=True)
        save_dir(p)
        return p

    if opt == "3":
        paths = load_saved_dirs()
        for i, p in enumerate(paths, 1):
            print(f"{i} - {p}")
        idx = int(input("Escolha o número: ").strip())
        return Path(paths[idx - 1])

    sys.exit("❌ Opção inválida")

# ======================================================
# CORE
# ======================================================
def download_youtube(
    url: str,
    output_dir: Path,
    partition: bool,
    t_ini: int | None,
    t_end: int | None,
    custom_name: str | None,
    download_subs: bool,
    max_quality: bool
):
    output_template = "%(title).200s.%(ext)s"
    if custom_name:
        output_template = f"{custom_name}.%(ext)s"

    selected_format = MAX_QUALITY_FORMAT if max_quality else FORMAT

    command = [
        sys.executable, "-m", "yt_dlp",
        "--js-runtimes", f"node:{NODE_PATH}",
        "-f", selected_format,
        "--merge-output-format", MERGE_FORMAT,
        "--ignore-errors",
        "--no-playlist",
        "--force-overwrites",
        "--no-part",
        "-o", str(output_dir / output_template),
    ]

    if download_subs:
        command += [
            "--write-subs",
            "--write-auto-subs",
            "--sub-langs", f"{PRIMARY_SUB_LANG},{FALLBACK_SUB_LANG}",
            "--sub-format", "srt",
            "--convert-subs", "srt",
        ]

    if partition:
        command += ["--download-sections", f"*{t_ini}-{t_end}"]

    command.append(url)
    subprocess.run(command, check=True)

    if download_subs and partition:
        for srt in output_dir.glob(f"{custom_name or '*'}*.srt"):
            trim_srt(srt, t_ini, t_end)

# ======================================================
# MAIN
# ======================================================
if __name__ == "__main__":

    print("\nModo de operação:")
    print("1 - Download único")
    print("2 - Download em lote (arquivo .txt)")

    mode = input("Escolha (1/2): ").strip()

    output_dir = choose_output_dir()

    partition = input("Deseja particionar o vídeo? (s/n): ").strip().lower() == "s"
    t_ini = t_end = None

    if partition:
        try:
            t_ini = parse_time_input(input("t_ini (segundos ou HH:MM:SS): "))
            t_end = parse_time_input(input("t_end (segundos ou HH:MM:SS): "))
            if t_end <= t_ini:
                raise ValueError
        except ValueError:
            sys.exit("❌ Tempo inválido")

    name_input = input("Nome do arquivo (ou 'n' para usar o padrão): ").strip()
    custom_name = None if name_input.lower() == "n" else name_input

    download_subs = input("Deseja baixar a legenda? (s/n): ").strip().lower() == "s"

    max_quality = input("Qualidade máxima absoluta? (s/n): ").strip().lower() == "s"

    # ==========================================
    # DOWNLOAD ÚNICO
    # ==========================================
    if mode == "1":
        url = input("Informe a URL do YouTube: ").strip()

        download_youtube(
            url=url,
            output_dir=output_dir,
            partition=partition,
            t_ini=t_ini,
            t_end=t_end,
            custom_name=custom_name,
            download_subs=download_subs,
            max_quality=max_quality
        )

    # ==========================================
    # DOWNLOAD EM LOTE
    # ==========================================
    elif mode == "2":
        txt_path = Path(input("Informe o caminho do arquivo .txt: ").strip())

        if not txt_path.exists():
            sys.exit("❌ Arquivo não encontrado")

        urls = [
            line.strip()
            for line in txt_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

        print(f"\n🔹 {len(urls)} vídeos encontrados.\n")

        for i, url in enumerate(urls, 1):
            print(f"▶ [{i}/{len(urls)}] Baixando: {url}")
            try:
                download_youtube(
                    url=url,
                    output_dir=output_dir,
                    partition=partition,
                    t_ini=t_ini,
                    t_end=t_end,
                    custom_name=None,
                    download_subs=download_subs,
                    max_quality=max_quality
                )
            except Exception as e:
                print(f"⚠ Erro ao baixar: {e}")

    else:
        sys.exit("❌ Opção inválida")