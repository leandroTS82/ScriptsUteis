r"""
===============================================================
 Script: BatchMakeVideos.py
 Autor: Leandro
 Versão: Integrada ao novo sistema ContentCreated + Subpastas
===============================================================
📌 O que este script faz?
---------------------------------------------------------------
Executa o MakeVideo.py em modo LOTE.

FUNCIONALIDADES:
 • Aceita execução com OU sem argumento
 • Se não informar argumento → usa DEFAULT_ROOT: ./ContentToCreate
 • Varre todas as subpastas recursivamente
 • Ignora arquivos já processados (uploaded_, moved_, ToGroq_, Created_)
 • Copia cada JSON → textos.json
 • Registra o arquivo atual em CURRENT_JSON_PATH.txt
 • Executa MakeVideo.py para cada JSON
===============================================================
"""

import os
import sys
import shutil
import subprocess

MAKEVIDEO_SCRIPT = "MakeVideo.py"
TEMP_TEXTOS_FILE = "textos.json"

# prefixos ignorados → arquivos já processados/movidos
IGNORED_PREFIXES = [
    "uploaded_", "moved_", "ToGroq_", "Created_"
]

# Diretório padrão se nenhum argumento for informado
DEFAULT_ROOT = "C:\\dev\\scripts\\ScriptsUteis\\Python\\ContentFabric\\1GroqIA_WordBank\\2ContentToCreate"


def collect_all_json_files(root_dir):
    """
    Varre root_dir e TODAS subpastas recursivamente.
    Retorna lista de JSONs válidos para processar.
    """
    json_paths = []

    for current_dir, _, files in os.walk(root_dir):
        for f in files:
            if f.lower().endswith(".json") and not any(
                f.startswith(prefix) for prefix in IGNORED_PREFIXES
            ):
                json_paths.append(os.path.join(current_dir, f))

    return json_paths


def run_batch(json_root: str):
    """
    Executa MakeVideo.py para todos os JSONs encontrados recursivamente.
    """
    if not os.path.isdir(json_root):
        print(f"❌ Diretório '{json_root}' não encontrado.")
        return

    json_files = collect_all_json_files(json_root)

    if not json_files:
        print(f"⚠ Nenhum arquivo JSON válido encontrado em {json_root}")
        return

    print(f"📂 {len(json_files)} arquivos para processar.\n")

    for idx, json_path in enumerate(sorted(json_files), start=1):
        json_file = os.path.basename(json_path)

        print("=" * 80)
        print(f"▶️  ({idx}/{len(json_files)}) Processando: {json_file}")
        print(f"📍 Caminho: {json_path}")
        print("=" * 80)

        # Copiar JSON → textos.json
        try:
            shutil.copy(json_path, TEMP_TEXTOS_FILE)
        except Exception as e:
            print(f"❌ Erro ao copiar {json_file}: {e}")
            continue

        # Registrar JSON em uso (MakeVideo lê esse arquivo)
        with open("CURRENT_JSON_PATH.txt", "w", encoding="utf-8") as f:
            f.write(json_path)

        # Executar MakeVideo
        try:
            subprocess.run(["python", MAKEVIDEO_SCRIPT], check=True)
            print(f"✅ Finalizado: {json_file}\n")
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao processar {json_file}: {e}\n")

    print("🎬 Todos os arquivos foram processados com sucesso!")


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        # Modo com argumento
        target_dir = sys.argv[1]
        print(f"📌 Diretório informado: {target_dir}")
        run_batch(target_dir)
    else:
        # Modo automático
        print("📌 Nenhum diretório informado. Usando diretório padrão:")
        print(f"➡ {DEFAULT_ROOT}\n")
        run_batch(DEFAULT_ROOT)
