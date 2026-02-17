import os
import time
import socket
import shutil
import threading
import re
import sys
import hashlib
import webbrowser
import json
from http.server import SimpleHTTPRequestHandler
from socketserver import ThreadingTCPServer
from PyPDF2 import PdfReader
from itertools import cycle
import random
import requests

# ==========================================================
# CONFIG
# ==========================================================

sys.path.append(r"C:\dev\scripts\ScriptsUteis\Python\EKF_EnglishKnowledgeFramework")
from Services.image_generation_service import ImageGenerationService


BASE_DIR = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\EKF_EnglishKnowledgeFramework_REPO\View_PDF"

WEB_PDFS_DIR = os.path.join(BASE_DIR, "_web_pdfs")
WEB_IMAGES_DIR = os.path.join(BASE_DIR, "_web_images")
CACHE_FILE = os.path.join(BASE_DIR, "pdf_index_cache.json")
CONTEXT_CACHE_FILE = os.path.join(BASE_DIR, "image_context_cache.json")
SUMMARY_CACHE_FILE = os.path.join(BASE_DIR, "summary_ai_cache.json")
INDEX_HTML = os.path.join(BASE_DIR, "index.html")

MAX_IMAGES_PER_RUN = 5
SUMMARY_MAX_CHARS = 8000

# ==========================================================
# GROQ MULTI-KEY CONFIG (PADRÃO EKF)
# ==========================================================

GROQ_BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if GROQ_BASE not in sys.path:
    sys.path.insert(0, GROQ_BASE)
from groq_keys_loader import GROQ_KEYS
# ================================================================================
# CONFIG - GROQ MULTI KEYS (ROTATION / RANDOM)
# ================================================================================
_groq_key_cycle = cycle(random.sample(GROQ_KEYS, len(GROQ_KEYS)))


GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b"

PDF_PATHS = [
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\EKF_EnglishKnowledgeFramework_REPO\Handouts\pdf",
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\EKF_EnglishKnowledgeFramework_REPO\BaseTerms",
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\EnglishReview",
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\EnglishReview\stories_compilation"
]

WEB_PDFS_DIR = os.path.join(BASE_DIR, "_web_pdfs")
WEB_IMAGES_DIR = os.path.join(BASE_DIR, "_web_images")
INDEX_HTML = os.path.join(BASE_DIR, "index.html")
CACHE_FILE = os.path.join(BASE_DIR, "pdf_index_cache.json")


# ==========================================================
# GROQ KEY HANDLING (SUPPORTS {"name": "...", "key": "..."} )
# ==========================================================

def get_next_groq_key():
    """
    Supports:
    - list[str]
    - list[{"key": "..."}]
    - list[{"name": "...", "key": "..."}]
    """

    for _ in range(len(GROQ_KEYS)):
        candidate = next(_groq_key_cycle)

        # If dict
        if isinstance(candidate, dict):
            key = candidate.get("key", "").strip()
        else:
            key = str(candidate).strip()

        if key.startswith("gsk_"):
            return key

    raise RuntimeError("❌ No valid GROQ key found.")


def call_groq_summary(prompt_text):

    last_error = None

    for _ in range(len(GROQ_KEYS)):

        api_key = get_next_groq_key()

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {"role": "user", "content": prompt_text}
            ],
            "temperature": 0.7,
            "max_tokens": 1200
        }

        try:
            response = requests.post(
                GROQ_URL,
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 429:
                last_error = "Rate limit"
                continue

            response.raise_for_status()

            data = response.json()

            if "choices" not in data:
                continue

            content = data["choices"][0]["message"]["content"]

            if content and len(content.strip()) > 20:
                return content.strip()

        except requests.RequestException as e:
            last_error = str(e)
            continue

    print(f"❌ All GROQ keys failed. Last error: {last_error}")
    return None


# ==========================================================
# CACHE
# ==========================================================

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_cache(data):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
def load_context_cache():
    if os.path.exists(CONTEXT_CACHE_FILE):
        with open(CONTEXT_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_context_cache(data):
    os.makedirs(os.path.dirname(CONTEXT_CACHE_FILE), exist_ok=True)
    with open(CONTEXT_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_summary_cache():
    if os.path.exists(SUMMARY_CACHE_FILE):
        with open(SUMMARY_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_summary_cache(data):
    os.makedirs(os.path.dirname(SUMMARY_CACHE_FILE), exist_ok=True)
    with open(SUMMARY_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ==========================================================
# HELPERS
# ==========================================================

def slugify(text):
    return "".join(c.lower() if c.isalnum() else "_" for c in text)

def format_display_name(filename):
    name = filename.replace(".pdf", "")
    if len(name) > 13 and name[:12].isdigit() and name[12] == "_":
        name = name[13:]
    return name.replace("_", " ").title()

def folder_title(path):
    return os.path.basename(os.path.normpath(path)) or path

def get_free_port():
    s = socket.socket()
    s.bind(("", 0))
    port = s.getsockname()[1]
    s.close()
    return port

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

# ==========================================================
# PDF EXTRACTION
# ==========================================================

def extract_pdf_text(path):
    try:
        reader = PdfReader(path)
        text = ""
        for page in reader.pages[:3]:
            text += page.extract_text() or ""
        return text.lower()
    except:
        return ""

# ==========================================================
# TERM EXTRACTION
# ==========================================================

def extract_terms_from_text(text, max_terms=1):
    text = re.sub(r'\s+', ' ', text)
    candidates = re.findall(r'\b(?:[A-Za-z]{3,}\s){1,4}[A-Za-z]{3,}\b', text)

    seen = set()
    results = []

    for c in candidates:
        c = c.strip().lower()
        if c not in seen and 2 <= len(c.split()) <= 5:
            seen.add(c)
            results.append(c)

    return results[:max_terms]

# ==========================================================
# IMAGE GENERATION (COM CACHE)
# ==========================================================

def safe_parse_date(date_str):
    try:
        return time.mktime(time.strptime(date_str, "%d/%m/%Y %H:%M"))
    except:
        return 0


def consolidate_recent_terms(sections, limit=MAX_IMAGES_PER_RUN):

    all_items = []

    for sec in sections:
        for item in sec["items"]:
            all_items.append(item)

    # Ordena por data mais recente
    all_items.sort(
        key=lambda x: safe_parse_date(x["modified"]),
        reverse=True
    )

    unique_terms = []
    seen = set()

    for item in all_items:
        terms = extract_terms_from_text(item["content"])
        if terms:
            term = terms[0]
            if term not in seen:
                seen.add(term)
                unique_terms.append(term)

        if len(unique_terms) >= limit:
            break

    return unique_terms

def generate_images_for_recent_terms(recent_terms):

    os.makedirs(WEB_IMAGES_DIR, exist_ok=True)

    context_cache = load_context_cache()
    generated = {}

    generated_count = 0

    for term in recent_terms:

        slug = slugify(term)
        filename = slug + ".jpg"
        output_path = os.path.join(WEB_IMAGES_DIR, filename)

        # Se já existe → apenas reutiliza
        if os.path.exists(output_path):
            generated[term] = filename
            context_cache[term] = filename
            continue

        # Limite de geração por execução
        if generated_count >= MAX_IMAGES_PER_RUN:
            continue

        prompt = f"""
        Create a modern educational illustration (with black people in the style spider-verse) representing:
        "{term}"

        Clean layout, minimalistic, academic style,
        vector art, high clarity.
        """

        try:
            image_service.generate(
                prompt=prompt,
                output_path=output_path,
                mode="landscape"
            )

            context_cache[term] = filename
            generated[term] = filename
            generated_count += 1

        except Exception as e:
            print("⚠ Erro imagem:", e)

    save_context_cache(context_cache)
    return generated


# ==========================================================
# SCAN SECTIONS
# ==========================================================
API_KEY_PATH = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\FilesHelper\secret_tokens_keys\google-gemini-key.txt"

def load_api_key():
    return open(API_KEY_PATH).read().strip()

image_service = ImageGenerationService(load_api_key())

def scan_sections():

    cache = load_cache()
    updated_cache = {}
    sections = []

    print("📦 Carregando cache...")

    for path in PDF_PATHS:

        title = folder_title(path)
        slug = slugify(title)
        items = []

        if os.path.exists(path):

            files = [f for f in os.listdir(path) if f.lower().endswith(".pdf")]

            files.sort(
                key=lambda f: os.path.getmtime(os.path.join(path, f)),
                reverse=True
            )

            for pdf in files:

                full = os.path.join(path, pdf)
                mtime = os.path.getmtime(full)
                size = os.path.getsize(full)

                cache_key = full

                if cache_key in cache and \
                   cache[cache_key]["mtime"] == mtime and \
                   cache[cache_key]["size"] == size:

                    content = cache[cache_key]["content"]
                else:
                    print("🔄 Atualizando:", pdf)
                    content = extract_pdf_text(full)

                updated_cache[cache_key] = {
                    "mtime": mtime,
                    "size": size,
                    "content": content
                }

                illustration = None
                terms = extract_terms_from_text(content)
                if terms:
                    illustration = terms[0]

                items.append({
                    "file": pdf,
                    "full_path": full,
                    "display": format_display_name(pdf),
                    "size": size // 1024,
                    "modified": time.strftime(
                        "%d/%m/%Y %H:%M",
                        time.localtime(mtime)
                    ),
                    "content": content,
                    "illustration": illustration
                })

        if items:
            sections.append({
                "title": title,
                "slug": slug,
                "items": items
            })

    save_cache(updated_cache)

    return sections

# ==========================================================
# PREP WEB FILES
# ==========================================================

def prepare_web_files(sections):

    os.makedirs(WEB_PDFS_DIR, exist_ok=True)
    os.makedirs(WEB_IMAGES_DIR, exist_ok=True)

    for sec in sections:
        sec_dir = os.path.join(WEB_PDFS_DIR, sec["slug"])
        os.makedirs(sec_dir, exist_ok=True)

        for item in sec["items"]:
            dest = os.path.join(sec_dir, item["file"])
            if not os.path.exists(dest):
                shutil.copy2(item["full_path"], dest)

# ==========================================================
# HTML GENERATION
# ==========================================================

def generate_global_summary(sections):

    cache = load_summary_cache()

    # Consolidar conteúdo real já extraído
    consolidated_text = ""

    for sec in sections:
        for item in sec["items"]:
            if item.get("content"):
                consolidated_text += item["content"][:500] + "\n\n"

            if len(consolidated_text) > SUMMARY_MAX_CHARS:
                break

    content_hash = hashlib.md5(consolidated_text.encode()).hexdigest()

    if content_hash in cache:
        return cache[content_hash]

    enriched_prompt = f"""
        You are an yonger, modern advanced English educator.

        Based on the following real extracted study material,
        generate a coherent, structured learning summary.

        The summary MUST:

        - Be logically organized
        - Be didactic
        - Include EN + PT explanation
        - Include example sentences, similar expressions, usages, phrasal verbs (when applicable), common expressions, and others.
        - Include grammar insight, tips.
        - Include level progression (A1 → B1 if applicable)

        Structure it like a mini study material page.

        CONTENT:
        {consolidated_text}
        """

    print("🧠 Generating structured study summary via Groq...")

    result = call_groq_summary(enriched_prompt)

    if result:
        cache[content_hash] = result
        save_summary_cache(cache)
        return result

    return "Summary unavailable."



def generate_html(sections):

    summary_text = generate_global_summary(sections)

    toggle_script = """
        <script>
        function toggleContent(id){
            var el = document.getElementById(id);
            if(el.style.display === "none"){
                el.style.display = "block";
            } else {
                el.style.display = "none";
            }
        }
        </script>
        """

    html_sections = ""

    for sec in sections:

        cards = ""

        for item in sec["items"]:

            url = "_web_pdfs/" + sec["slug"] + "/" + item["file"]
            search_data = (item["display"] + " " + item["content"]).lower().replace('"', "'")

            image_block = ""
            if item.get("illustration"):
                image_block = (
                    f'<img src="_web_images/{item["illustration"]}" '
                    'class="img-fluid rounded mb-2" '
                    'style="height:200px;object-fit:cover;width:100%;">'
                )

            cards += f"""
                <div class="col-md-4 pdf-card" data-search="{search_data}">
                <div class="card shadow-sm border-0 h-100">
                <div class="card-body d-flex flex-column">
                {image_block}
                <div class="fw-bold mb-1">{item["display"]}</div>
                <div class="small text-muted mb-3">{item["size"]} KB · {item["modified"]}</div>
                <a class="btn btn-primary btn-sm mt-auto" href="{url}" target="_blank">📖 Abrir PDF</a>
                </div>
                </div>
                </div>
                """

        html_sections += f"""
            <section class="mb-5">
            <h4 style="cursor:pointer;" onclick="toggleContent('{sec["slug"]}')">
            📁 {sec["title"]} ({len(sec["items"])})
            </h4>
            <div id="{sec["slug"]}" style="display:none;">
            <div class="row g-3">
            {cards}
            </div>
            </div>
            </section>
            """

    summary_block = f"""
        <div class="card shadow-lg border-0 mb-5">
        <div class="card-body">
        <h4>📘 AI Study Overview</h4>
        <button class="btn btn-sm btn-outline-secondary mb-3"
        onclick="toggleContent('summaryContent')">Toggle Summary</button>
        <div id="summaryContent" style="white-space:pre-line;line-height:1.7;">
        {summary_text}
        </div>
        </div>
        </div>
        """

    html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="UTF-8">
        <title>EKF Study Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body class="bg-light">

        <div class="container py-5">

        <h2 class="mb-4">📚 English Knowledge Framework</h2>

        {summary_block}

        <input id="searchInput" class="form-control mb-4" placeholder="Search PDFs...">

        {html_sections}

        </div>

        {toggle_script}

        <script>
        document.getElementById("searchInput").addEventListener("keyup", function() {{
            let value = this.value.toLowerCase();
            document.querySelectorAll(".pdf-card").forEach(function(card) {{
                let text = card.getAttribute("data-search");
                card.style.display = text.includes(value) ? "block" : "none";
            }});
        }});
        </script>

        </body>
        </html>
        """

    with open(INDEX_HTML, "w", encoding="utf-8") as f:
        f.write(html)



# ==========================================================
# SERVER
# ==========================================================

def start_server(port):
    os.chdir(BASE_DIR)

    class Handler(SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            return

    ThreadingTCPServer.allow_reuse_address = True

    with ThreadingTCPServer(("0.0.0.0", port), Handler) as httpd:
        httpd.serve_forever()

# ==========================================================
# MAIN
# ==========================================================

def main():

    print("🔎 Escaneando PDFs...")
    sections = scan_sections()
    
    print("🧠 Consolidando termos recentes...")
    recent_terms = consolidate_recent_terms(sections)

    print("🎨 Gerando imagens apenas para 5 termos mais recentes...")
    generated_map = generate_images_for_recent_terms(recent_terms)

    # Associar imagens aos itens
    for sec in sections:
        for item in sec["items"]:
            term = item.get("illustration")
            if term and term in generated_map:
                item["illustration"] = generated_map[term]
            else:
                item["illustration"] = None

    print("📦 Preparando arquivos web...")
    prepare_web_files(sections)

    print("📝 Gerando HTML...")
    generate_html(sections)

    port = get_free_port()
    ip = get_local_ip()

    threading.Thread(
        target=start_server,
        args=(port,),
        daemon=True
    ).start()

    time.sleep(1)

    url = "http://{}:{}/index.html".format(ip, port)

    print("\n🌐 Interface pronta!")
    print("👉 Acesse:", url)

    webbrowser.open(url)

    input("\nPressione ENTER para encerrar...")

if __name__ == "__main__":
    main()
