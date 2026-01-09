# ============================================================
# media_search_v23.py
# Media Search - Mobile Responsive UI
# ============================================================

import sys
import os
import urllib.parse
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, HTTPServer
from datetime import datetime

HOST = "127.0.0.1"
PORT = 8000
OUTPUT_HTML = "index.html"

MEDIA_EXT = (".mp4", ".mov", ".mp3", ".wav", ".aac", ".flac", ".ogg")
VIDEO_EXT = (".mp4", ".mov")
AUDIO_EXT = (".mp3", ".wav", ".aac", ".flac", ".ogg")


class MediaHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        if path.startswith("/media/"):
            return urllib.parse.unquote(path.replace("/media/", ""))
        return super().translate_path(path)


def search_media(paths, term):
    results = []
    for base in paths:
        if not os.path.exists(base):
            continue

        for root, _, files in os.walk(base):
            for f in files:
                if f.lower().endswith(MEDIA_EXT) and term in f.lower():
                    results.append(os.path.join(root, f))
    return results


def player_html(path):
    url = "/media/" + urllib.parse.quote(path.replace("\\", "/"))
    ext = os.path.splitext(path)[1].lower()

    if ext in VIDEO_EXT:
        return f'<video controls preload="metadata" src="{url}"></video>'
    return f'<audio controls preload="metadata" src="{url}"></audio>'


def generate_html(term, results):
    cards = []

    for path in results:
        cards.append(f"""
        <div class="card">
            <div class="title">{os.path.basename(path)}</div>
            {player_html(path)}
            <div class="path">{path}</div>
        </div>
        """)

    return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Media Search</title>

<style>
:root {{
    --bg: #0f172a;
    --card: #020617;
    --text: #e5e7eb;
    --muted: #94a3b8;
}}

body {{
    margin: 0;
    padding: 16px;
    background: var(--bg);
    color: var(--text);
    font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
}}

h1 {{
    font-size: 1.2rem;
    margin-bottom: 4px;
}}

small {{
    color: var(--muted);
}}

.grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 16px;
    margin-top: 16px;
}}

.card {{
    background: var(--card);
    border-radius: 14px;
    padding: 14px;
    box-shadow: 0 0 0 1px rgba(255,255,255,0.05);
}}

.title {{
    font-size: 0.95rem;
    margin-bottom: 8px;
    word-break: break-word;
}}

video, audio {{
    width: 100%;
    margin: 8px 0;
}}

.path {{
    font-size: 0.7rem;
    color: var(--muted);
    word-break: break-all;
}}

</style>
</head>

<body>

<h1>🔎 "{term}"</h1>
<small>{len(results)} resultado(s) • {datetime.now():%d/%m/%Y %H:%M:%S}</small>

<div class="grid">
{''.join(cards)}
</div>

</body>
</html>
"""


def start_server():
    HTTPServer((HOST, PORT), MediaHandler).serve_forever()


def main():
    if len(sys.argv) < 2:
        print("Informe paths via parâmetro.")
        return

    paths = sys.argv[1:]
    term = input("Digite o termo: ").strip().lower()
    if not term:
        return

    results = search_media(paths, term)
    if not results:
        print("Nenhum resultado.")
        return

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(generate_html(term, results))

    threading.Thread(target=start_server, daemon=True).start()

    url = f"http://{HOST}:{PORT}/{OUTPUT_HTML}"
    print("Abrindo:", url)
    webbrowser.open(url)

    input("Servidor ativo. ENTER para sair.")


if __name__ == "__main__":
    main()
