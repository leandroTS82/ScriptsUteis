import subprocess
import sys
from pathlib import Path
from datetime import timedelta

# ======================================================
# CONFIG ANDROID
# ======================================================
OUTPUT_DIR = Path("/storage/emulated/0/Download/youtube_clips")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FORMAT = "18/best"  # MP4 estável no Android
PRIMARY_SUB_LANG = "pt"
FALLBACK_SUB_LANG = "en"

COOKIES_FILE = Path("/storage/emulated/0/Download/cookies.txt")
USE_COOKIES = COOKIES_FILE.exists()

# ======================================================
# UTILS – TEMPO FLEXÍVEL
# ======================================================
def parse_time_input(value: str) -> int:
    """
    Aceita:
      - segundos: 120
      - MM:SS    : 02:00
      - HH:MM:SS : 01:02:03
    Retorna segundos (int)
    """
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
# SRT UTILS
# ======================================================
def parse_srt_time(t):
    h, m, s_ms = t.split(":")
    s, ms = s_ms.split(",")
    return timedelta(
        hours=int(h),
        minutes=int(m),
        seconds=int(s),
        milliseconds=int(ms)
    )

def format_srt_time(td):
    total_ms = int(td.total_seconds() * 1000)
    ms = total_ms % 1000
    total_s = total_ms // 1000
    s = total_s % 60
    total_m = total_s // 60
    m = total_m % 60
    h = total_m // 60
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def trim_srt(path, t_ini, t_end):
    start = timedelta(seconds=t_ini)
    end = timedelta(seconds=t_end)

    blocks = path.read_text(encoding="utf-8").split("\n\n")
    out = []
    idx = 1

    for block in blocks:
        lines = block.strip().splitlines()
        if len(lines) < 3:
            continue

        try:
            t1, t2 = lines[1].split(" --> ")
        except ValueError:
            continue

        a = parse_srt_time(t1)
        b = parse_srt_time(t2)

        if b < start or a > end:
            continue

        a = max(a, start) - start
        b = min(b, end) - start

        out.append("\n".join([
            str(idx),
            f"{format_srt_time(a)} --> {format_srt_time(b)}",
            *lines[2:]
        ]))
        idx += 1

    path.write_text("\n\n".join(out), encoding="utf-8")

# ======================================================
# MAIN
# ======================================================
url = input("URL do YouTube: ").strip()
if not url.startswith("http"):
    sys.exit("❌ URL inválida")

partition = input("Deseja cortar? (s/n): ").strip().lower() == "s"
t_ini = t_end = None

if partition:
    try:
        t_ini = parse_time_input(input("t_ini (segundos ou HH:MM:SS): "))
        t_end = parse_time_input(input("t_end (segundos ou HH:MM:SS): "))
        if t_end <= t_ini:
            raise ValueError
    except ValueError:
        sys.exit("❌ Tempo inválido")

name_input = input("Nome do arquivo (ou 'n'): ").strip()
custom_name = None if name_input.lower() == "n" else name_input

output_tpl = "%(title)s.%(ext)s"
if custom_name:
    output_tpl = f"{custom_name}.%(ext)s"

# ======================================================
# yt-dlp COMMAND
# ======================================================
cmd = [
    sys.executable, "-m", "yt_dlp",
    "-f", FORMAT,
    "--no-playlist",
    "--ignore-errors",
    "-o", str(OUTPUT_DIR / output_tpl),
]

if USE_COOKIES:
    cmd += ["--cookies", str(COOKIES_FILE)]

cmd += [
    "--write-subs",
    "--write-auto-subs",
    "--sub-langs", f"{PRIMARY_SUB_LANG},{FALLBACK_SUB_LANG}",
    "--sub-format", "srt",
    "--convert-subs", "srt",
]

if partition:
    cmd += ["--download-sections", f"*{t_ini}-{t_end}"]

cmd.append(url)

print("\n▶ Iniciando download...\n")
subprocess.run(cmd, check=True)

# ======================================================
# CORTE REAL DA LEGENDA
# ======================================================
if partition:
    for srt in OUTPUT_DIR.glob("*.srt"):
        trim_srt(srt, t_ini, t_end)

print("\n✔ Concluído")
print(f"📁 Arquivos em: {OUTPUT_DIR}")
