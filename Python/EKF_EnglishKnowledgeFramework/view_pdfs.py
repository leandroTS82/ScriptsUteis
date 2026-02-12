import os
import time
import socket
import shutil
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler
from socketserver import ThreadingTCPServer
from PyPDF2 import PdfReader

# ==========================================================
# CONFIG
# ==========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\EKF_EnglishKnowledgeFramework_REPO"
PDF_PATHS = [
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\EKF_EnglishKnowledgeFramework_REPO\Handouts\pdf",
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\EKF_EnglishKnowledgeFramework_REPO\BaseTerms",
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\EnglishReview",
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\EnglishReview\stories_compilation"
]

WEB_PDFS_DIR = os.path.join(BASE_DIR, "_web_pdfs")
INDEX_HTML = os.path.join(BASE_DIR, "index.html")


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
# EXTRAIR TEXTO PDF (para busca interna)
# ==========================================================

def extract_pdf_text(path):
    try:
        reader = PdfReader(path)
        text = ""
        for page in reader.pages[:3]:  # limite para performance
            text += page.extract_text() or ""
        return text.lower()
    except:
        return ""


# ==========================================================
# SCAN SECTIONS
# ==========================================================

def scan_sections():
    sections = []

    for path in PDF_PATHS:
        title = folder_title(path)
        slug = slugify(title)
        items = []

        if os.path.exists(path):
            files = [f for f in os.listdir(path) if f.lower().endswith(".pdf")]

            # MAIS RECENTE PRIMEIRO
            files.sort(
                key=lambda f: os.path.getmtime(os.path.join(path, f)),
                reverse=True
            )

            for pdf in files:
                full = os.path.join(path, pdf)

                items.append({
                    "file": pdf,
                    "full_path": full,
                    "display": format_display_name(pdf),
                    "size": os.path.getsize(full) // 1024,
                    "modified": time.strftime(
                        "%d/%m/%Y %H:%M",
                        time.localtime(os.path.getmtime(full))
                    ),
                    "content": extract_pdf_text(full)
                })

        sections.append({
            "title": title,
            "slug": slug,
            "items": items
        })

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

def generate_html(sections):

    html_sections = ""

    for sec in sections:

        cards = ""

        for item in sec["items"]:
            url = f"_web_pdfs/{sec['slug']}/{item['file']}"

            cards += f"""
            <div class="col-12 col-md-6 col-lg-4 pdf-card"
                 data-search="{(item['display'] + ' ' + item['content']).lower()}">
              <div class="card shadow-sm border-0 h-100">
                <div class="card-body d-flex flex-column">
                  <div class="fw-bold mb-1 text-truncate">{item['display']}</div>
                  <div class="small text-muted mb-3">
                    {item['size']} KB · {item['modified']}
                  </div>
                  <a class="btn btn-primary btn-sm mt-auto"
                     href="{url}"
                     target="_blank">
                     📖 Abrir PDF
                  </a>
                </div>
              </div>
            </div>
            """

        html_sections += f"""
        <section class="mb-4">
          <div class="d-flex justify-content-between align-items-center mb-2">
            <h5 class="m-0 toggle-header" style="cursor:pointer;">
              📁 {sec['title']} <span class="toggle-icon">➕</span>
            </h5>
            <span class="badge bg-primary">{len(sec['items'])}</span>
          </div>

          <div class="row g-3 section-content hidden-section">
            {cards}
          </div>
        </section>
        """

    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>📚 PDF Viewer</title>

<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>

<style>
body {{
    background: linear-gradient(120deg, #f4f6f9, #eef2f7);
}}

.hidden-section {{
    display:none;
}}

.text-truncate {{
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}}
</style>
</head>

<body>

<div class="container py-4">

<h3 class="mb-4">📚 Seus PDFs</h3>

<input id="searchInput"
       class="form-control mb-4"
       placeholder="🔎 Buscar por nome ou conteúdo...">

<div id="resultCounter" class="small text-muted mb-3"></div>

{html_sections}

</div>

<script>

$(function(){{

  function updateCounter() {{
      let visible = $(".pdf-card:visible").length;
      $("#resultCounter").text(visible + " resultado(s) encontrados");
  }}

  updateCounter();

  // 🔎 SEARCH
  $("#searchInput").on("keyup", function(){{
      let value = $(this).val().toLowerCase();

      $(".pdf-card").each(function(){{
          let text = $(this).data("search");
          $(this).toggle(text.includes(value));
      }});

      updateCounter();
  }});

  // 📁 TOGGLE SECTION
  $(".toggle-header").on("click", function(){{
      let section = $(this).closest("section").find(".section-content");
      let icon = $(this).find(".toggle-icon");

      section.toggleClass("hidden-section");

      if(section.hasClass("hidden-section")) {{
          icon.text("➕");
      }} else {{
          icon.text("➖");
      }}
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

    print("📦 Preparando arquivos web...")
    prepare_web_files(sections)

    print("📝 Gerando HTML...")
    generate_html(sections)

    port = get_free_port()
    ip = get_local_ip()

    server_thread = threading.Thread(
        target=start_server,
        args=(port,),
        daemon=True
    )
    server_thread.start()

    time.sleep(1)

    url = f"http://{ip}:{port}/index.html"

    print("\n🌐 Interface pronta!")
    print("👉 Acesse:", url)

    try:
        webbrowser.open(url)
    except:
        pass

    input("\nPressione ENTER para encerrar...")


if __name__ == "__main__":
    main()