# ============================================================
# media_search_mobile.py
# Media Search SMART — IA On-Demand por Arquivo
# ============================================================

import sys
import os
import json
import random
import requests
import urllib.parse
import threading
import webbrowser
import re
from http.server import SimpleHTTPRequestHandler, HTTPServer
from datetime import datetime

# ============================================================
# CONFIG
# ============================================================

HOST = "127.0.0.1"
PORT = 8000

CACHE_FILE = "./media_search_cache.json"
OUTPUT_HTML = "index.html"

# -------- MEDIA PATHS --------
MEDIA_PATHS = [
    "./01-Vídeos Inglês Leandrinho",
    "./01-Vídeos Inglês Leandrinho/wordbank",
    "./01-Vídeos Inglês Leandrinho/Histories",
    "./",
    "../"
]

# -------- GROQ --------

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b"


from groq_keys_loader import GROQ_KEYS

# -------- MEDIA --------

MEDIA_EXT = (".mp4", ".mov", ".mp3", ".wav", ".aac", ".flac", ".ogg")

# ============================================================
# TERMINAL COLORS
# ============================================================

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"

# ============================================================
# HTTP SERVER
# ============================================================

class MediaHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        if path.startswith("/media/"):
            return urllib.parse.unquote(path.replace("/media/", ""))
        return super().translate_path(path)

# ============================================================
# CACHE
# ============================================================

def load_cache():
    if not os.path.exists(CACHE_FILE):
        return {}
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

# ============================================================
# GROQ
# ============================================================

def build_prompt(text: str) -> str:
    return f"""
Return ONLY valid JSON.

{{
  "english": "{text}",
  "translation_pt": "",
  "meaning_pt": "",
  "definition_en": "",
  "examples_en": ["", "", ""],
  "grammar_focus": "",
  "learning_tip_pt": ""
}}
"""

def call_groq(text: str) -> dict:
    key = random.choice(GROQ_KEYS)

    res = requests.post(
        GROQ_URL,
        headers={
            "Authorization": f"Bearer {key['key']}",
            "Content-Type": "application/json"
        },
        json={
            "model": GROQ_MODEL,
            "messages": [{"role": "user", "content": build_prompt(text)}],
            "temperature": 0.2
        },
        timeout=30
    )

    res.raise_for_status()

    raw = res.json()["choices"][0]["message"]["content"]
    json_text = raw[raw.find("{"): raw.rfind("}") + 1]

    data = json.loads(json_text)
    data["_key_used"] = key["name"]
    return data

# ============================================================
# NORMALIZAÇÃO
# ============================================================

def normalize_video_key(filename: str) -> str:
    name = os.path.splitext(filename)[0]
    name = re.sub(r"^uploaded_", "", name, flags=re.IGNORECASE)
    name = name.replace("_", " ")
    name = re.sub(r"\s+", " ", name).strip().lower()
    return name

# ============================================================
# ENRIQUECIMENTO
# ============================================================

def ensure_video_info(video_key: str, cache: dict) -> dict:
    cached = cache.get(video_key)

    if cached and cached.get("_status") == "enriched":
        return cached

    data = {
        "english": video_key,
        "translation_pt": "",
        "meaning_pt": "Informação não disponível (offline).",
        "definition_en": "",
        "examples_en": [],
        "grammar_focus": "",
        "learning_tip_pt": "",
        "_status": "anemic"
    }

    if cached:
        data.update(cached)

    print(f"{CYAN}🔁 IA on-demand → {video_key}{RESET}")

    try:
        enriched = call_groq(video_key)
        data.update(enriched)
        data["_status"] = "enriched"
        data["_last_enriched_at"] = datetime.now().isoformat()
        print(f"{GREEN}✅ Enriquecido{RESET}")
    except Exception as ex:
        print(f"{YELLOW}⚠️ IA falhou:{RESET}", ex)

    data["updated_at"] = datetime.now().isoformat()
    cache[video_key] = data
    save_cache(cache)

    return data

# ============================================================
# BUSCA DE MÍDIA (COM DEDUPLICAÇÃO)
# ============================================================

def search_media(paths, term):
    matches = []
    seen_files = set()

    for base in paths:
        if not os.path.exists(base):
            continue

        for root, _, files in os.walk(base):
            for f in files:
                fname = f.lower()

                if fname in seen_files:
                    continue

                if fname.endswith(MEDIA_EXT) and term.lower() in fname:
                    full = os.path.join(root, f)
                    matches.append(full)
                    seen_files.add(fname)

    return matches

def player_html(path):
    url = "/media/" + urllib.parse.quote(path.replace("\\", "/"))
    return f'<video controls preload="metadata" src="{url}"></video>'

# ============================================================
# UI
# ============================================================

def generate_html(items):
    cards = []
    modals = []

    for item in items:
        info = item["info"]
        key = item["key"]

        cards.append(f"""
        <div class="card">
            <div class="title">{item["filename"]}</div>
            {player_html(item["path"])}
            {f'<button onclick="openModal(`{key}`)">Detalhes</button>' if info["_status"]=="enriched" else ''}
            <div class="path">{item["path"]}</div>
        </div>
        """)

        if info["_status"] == "enriched":
            modals.append(f"""
            <div id="modal-{key}" class="modal">
              <div class="modal-content">
                <button onclick="closeModal(`{key}`)">Fechar</button>
                <h3>{key} — {info.get("translation_pt","")}</h3>
                <p>{info.get("meaning_pt","")}</p>
                <p><strong>Definição:</strong> {info.get("definition_en","")}</p>
                <p><strong>Gramática:</strong> {info.get("grammar_focus","")}</p>
                <ul>
                  {''.join(f"<li>{e}</li>" for e in info.get("examples_en", []))}
                </ul>
                <em>{info.get("learning_tip_pt","")}</em>
              </div>
            </div>
            """)

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Resultados</title>
<style>
body {{ background:#0f172a;color:#e5e7eb;font-family:system-ui;padding:16px; }}
.grid {{ display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px; }}
.card {{ background:#020617;padding:14px;border-radius:14px; }}
.title {{ font-weight:600; }}
video {{ width:100%;margin:8px 0; }}
button {{ width:100%;padding:10px;border:none;border-radius:10px;background:#2563eb;color:white;margin-top:8px; }}
.path {{ font-size:11px;color:#94a3b8;word-break:break-all; }}
.modal {{ display:none;position:fixed;inset:0;background:rgba(0,0,0,.7); }}
.modal-content {{ background:#020617;margin:8% auto;padding:20px;width:90%;max-width:520px;border-radius:14px; }}
</style>
<script>
function openModal(key) {{ document.getElementById("modal-" + key).style.display = "block"; }}
function closeModal(key) {{ document.getElementById("modal-" + key).style.display = "none"; }}
</script>
</head>
<body>
<h2>Resultados encontrados</h2>
<div class="grid">{''.join(cards)}</div>
{''.join(modals)}
</body>
</html>"""

# ============================================================
# MAIN
# ============================================================

def start_server():
    HTTPServer((HOST, PORT), MediaHandler).serve_forever()

def main():
    term = input("Digite o termo: ").strip().lower()
    if not term:
        return

    cache = load_cache()
    files = search_media(MEDIA_PATHS, term)

    if not files:
        print(f"{YELLOW}😕 Nenhum vídeo encontrado para:{RESET} {CYAN}{term}{RESET}")
        print(f"{GREEN}💡 Dica:{RESET} verifique o nome do arquivo ou tente outro termo.")
        return

    items = []

    for path in files:
        filename = os.path.basename(path)
        key = normalize_video_key(filename)

        info = ensure_video_info(key, cache)

        items.append({
            "key": key,
            "filename": filename,
            "path": path,
            "info": info
        })

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(generate_html(items))

    threading.Thread(target=start_server, daemon=True).start()
    webbrowser.open(f"http://{HOST}:{PORT}/{OUTPUT_HTML}")

    input("Servidor ativo. ENTER para sair.")

if __name__ == "__main__":
    main()
