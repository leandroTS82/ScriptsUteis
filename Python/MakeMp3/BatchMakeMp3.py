# C:\dev\scripts\ScriptsUteis\.venv\Scripts\Activate.ps1
import os
import shutil
import subprocess
import sys

# Caminhos base
base_dir = os.path.dirname(os.path.abspath(__file__))
fileSource_dir = os.path.join(base_dir, "WordBank_Vocabulary")  # pasta de origem 
textos_json = os.path.join(base_dir, "textos.json")
make_mp3_script = os.path.join(base_dir, "MakeMp3.py")
audios_juntos = os.path.join(base_dir, "audios", "juntos")

# Garantir que a pasta de saída exista
os.makedirs(audios_juntos, exist_ok=True)

# Lista todos os arquivos JSON na pasta BNN Book words
arquivos = [f for f in os.listdir(fileSource_dir) if f.endswith(".json")]
arquivos.sort()  # organiza pela ordem alfabética

for arquivo in arquivos:
    caminho_origem = os.path.join(fileSource_dir, arquivo)

    print(f"\n[PROCESSANDO] {arquivo}...")

    # Copiar conteúdo para textos.json
    shutil.copy(caminho_origem, textos_json)
    print(f"✔ Copiado {arquivo} para textos.json")

    # Executar MakeMp3.py no mesmo interpretador (venv)
    result = subprocess.run(
        [sys.executable, make_mp3_script],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print(f"✔ MakeMp3.py executado com sucesso para {arquivo}")

        # Nome esperado do arquivo de saída padrão (gerado pelo MakeMp3.py)
        mp3_saida = os.path.join(audios_juntos, "Unit9_Frases_TodosTempos.mp3")

        # Nome novo baseado no JSON de origem
        unidade_nome = arquivo.replace(".json", "_TodosTempos.mp3")
        mp3_destino = os.path.join(audios_juntos, unidade_nome)

        # Se o arquivo de saída existir, renomeia/move
        if os.path.exists(mp3_saida):
            # Se já existir um destino com o mesmo nome, remove para evitar conflito
            if os.path.exists(mp3_destino):
                os.remove(mp3_destino)

            shutil.move(mp3_saida, mp3_destino)
            print(f"Arquivo salvo como: {mp3_destino}")
        else:
            print("⚠ Não encontrei o MP3 gerado. Verifique o MakeMp3.py")

    else:
        print(f"Erro ao processar {arquivo}")
        print(result.stderr)
