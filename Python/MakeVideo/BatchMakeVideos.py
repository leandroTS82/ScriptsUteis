r"""
===============================================================
 Script: BatchMakeVideos.py
 Autor: Leandro
===============================================================
📌 O que este script faz?
---------------------------------------------------------------
Executa o MakeVideo.py em modo LOTE.

Para cada arquivo .json dentro de um diretório informado,
substitui temporariamente o "textos.json" padrão e executa
o MakeVideo.py, gerando um vídeo separado.

---------------------------------------------------------------
🧩 Estrutura esperada:
---------------------------------------------------------------
./meus_jsons/
    ├── aula1.json
    ├── aula2.json
    ├── aula3.json

---------------------------------------------------------------
⚙️ Execução:
---------------------------------------------------------------
    python .\BatchMakeVideos.py ./batch

O script:
  1️⃣ Localiza todos os .json dentro do diretório informado.
  2️⃣ Copia o conteúdo de cada um para "textos.json".
  3️⃣ Executa python .\MakeVideo.py.
  4️⃣ Move para o próximo arquivo automaticamente.
===============================================================
"""

import os
import sys
import shutil
import subprocess

# Nome do script principal
MAKEVIDEO_SCRIPT = "MakeVideo.py"
TEMP_TEXTOS_FILE = "textos.json"

def run_batch(json_dir: str):
    """Executa o MakeVideo.py para cada arquivo JSON no diretório informado."""

    if not os.path.isdir(json_dir):
        print(f"❌ Diretório '{json_dir}' não encontrado.")
        return

    json_files = [f for f in os.listdir(json_dir) if f.lower().endswith(".json")]
    if not json_files:
        print(f"⚠️ Nenhum arquivo .json encontrado em {json_dir}")
        return

    print(f"📂 {len(json_files)} arquivos .json encontrados em '{json_dir}'\n")

    for idx, json_file in enumerate(sorted(json_files), start=1):
        json_path = os.path.join(json_dir, json_file)
        print("="*80)
        print(f"▶️ ({idx}/{len(json_files)}) Processando: {json_file}")
        print("="*80)

        # Copia o conteúdo para textos.json (substitui temporariamente)
        try:
            shutil.copy(json_path, TEMP_TEXTOS_FILE)
        except Exception as e:
            print(f"❌ Erro ao copiar {json_file}: {e}")
            continue

        # Executa o MakeVideo.py
        try:
            subprocess.run(["python", MAKEVIDEO_SCRIPT], check=True)
            print(f"✅ Finalizado: {json_file}\n")
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao processar {json_file}: {e}\n")

    print("🎬 Todos os arquivos foram processados com sucesso!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python BatchMakeVideos.py <diretorio_com_jsons>")
        print("Exemplo: python BatchMakeVideos.py ./meus_jsons")
    else:
        run_batch(sys.argv[1])
