import os
import time
import socket
import shutil
import threading
import re
import sys
import webbrowser
import json
from http.server import SimpleHTTPRequestHandler
from socketserver import ThreadingTCPServer
from PyPDF2 import PdfReader

# ==========================================================
# CONFIG
# ==========================================================

sys.path.append(r"C:\dev\scripts\ScriptsUteis\Python\EKF_EnglishKnowledgeFramework")
from Services.image_generation_service import ImageGenerationService


BASE_DIR = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\EKF_EnglishKnowledgeFramework_REPO\View_PDF"

CONTEXT_CACHE_FILE = os.path.join(BASE_DIR, "image_context_cache.json")
MAX_IMAGES_PER_RUN = 5

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

    context_cache = load_context_cache()
    generated = {}

    for term in recent_terms:

        slug = slugify(term)
        filename = slug + ".jpg"
        output_path = os.path.join(WEB_IMAGES_DIR, filename)

        # 🔹 Se já existe no cache global → reaproveita
        if term in context_cache and os.path.exists(output_path):
            generated[term] = filename
            continue

        prompt = f"Create a clean modern educational illustration representing the expression '{term}'. Minimalistic, vibrant, expressive."

        try:
            image_service.generate(
                prompt=prompt,
                output_path=output_path,
                mode="landscape"
            )

            context_cache[term] = filename
            generated[term] = filename

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

    if os.path.exists(WEB_PDFS_DIR):
        shutil.rmtree(WEB_PDFS_DIR, ignore_errors=True)

    os.makedirs(WEB_PDFS_DIR, exist_ok=True)

    for sec in sections:
        sec_dir = os.path.join(WEB_PDFS_DIR, sec["slug"])
        os.makedirs(sec_dir, exist_ok=True)

        for item in sec["items"]:
            try:
                shutil.copy2(item["full_path"], os.path.join(sec_dir, item["file"]))
            except:
                pass

# ==========================================================
# HTML GENERATION
# ==========================================================

def generate_global_summary(sections, limit=20):

    all_text = ""

    for sec in sections:
        for item in sec["items"]:
            all_text += item["content"] + " "

    terms = extract_terms_from_text(all_text, max_terms=limit)

    return ", ".join(terms)

def generate_html(sections):

    summary_text = generate_global_summary(sections)
    html_sections = ""

    for sec in sections:

        cards = ""

        for item in sec["items"]:

            url = "_web_pdfs/" + sec["slug"] + "/" + item["file"]
            search_data = (item["display"] + " " + item["content"]).lower().replace('"', "'")

            image_block = ""

            if item.get("illustration"):
                image_block = (
                    '<img src="_web_images/' + item["illustration"] + '" '
                    'class="img-fluid rounded mb-2" '
                    'style="height:180px;object-fit:cover;width:100%;">'
                )

            cards += (
                '<div class="col-12 col-md-6 col-lg-4 pdf-card" '
                'data-search="' + search_data + '">'
                '<div class="card shadow-sm border-0 h-100">'
                '<div class="card-body d-flex flex-column">'
                + image_block +
                '<div class="fw-bold mb-1 text-truncate">' + item["display"] + '</div>'
                '<div class="small text-muted mb-3">'
                + str(item["size"]) + ' KB · ' + item["modified"] +
                '</div>'
                '<a class="btn btn-primary btn-sm mt-auto" '
                'href="' + url + '" target="_blank">'
                '📖 Abrir PDF'
                '</a>'
                '</div>'
                '</div>'
                '</div>'
            )

        html_sections += (
            '<section class="mb-4">'
            '<div class="d-flex justify-content-between align-items-center mb-2">'
            '<h5 class="m-0 toggle-header" style="cursor:pointer;">'
            '📁 ' + sec["title"] +
            '</h5>'
            '<span class="badge bg-primary">'
            + str(len(sec["items"])) +
            '</span>'
            '</div>'
            '<div class="row g-3 section-content" style="display:none;">'
            + cards +
            '</div>'
            '</section>'
        )

    html = (
        '<!DOCTYPE html>'
        '<html>'
        '<head>'
        '<meta charset="UTF-8">'
        '<title>PDF Viewer</title>'
        '<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">'
        '<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>'
        '</head>'
        '<body class="bg-light">'
        '<div class="container py-4">'
        '<h3 class="mb-2">📚 Seus PDFs</h3>'
        '<p class="text-muted small mb-4">'
        'Resumo de termos recentes: ' + summary_text +
        '</p>'
        '<input id="searchInput" class="form-control mb-3" placeholder="Buscar por nome ou conteúdo...">'
        + html_sections +
        '</div>'
        '<script>'
        '$("#searchInput").on("keyup", function() {'
        'let value = $(this).val().toLowerCase();'
        '$(".pdf-card").each(function() {'
        'let text = $(this).data("search");'
        '$(this).toggle(text.includes(value));'
        '});'
        '});'
        '$(".toggle-header").on("click", function() {'
        'let section = $(this).closest("section").find(".section-content");'
        'section.toggle();'
        '});'
        '</script>'
        '</body>'
        '</html>'
    )

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
