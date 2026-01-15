import os
import hashlib

# ==========================================================
# CONFIGURAÇÕES
# ==========================================================

VIDEOS_DIR = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\Videos"
PROCESSED_DIR = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\movies_processed"

# Flag: True = verifica conteúdo | False = apenas nome
CHECK_CONTENT = False

# ==========================================================
# FUNÇÕES AUXILIARES
# ==========================================================

def get_json_filenames(path: str) -> set[str]:
    return {
        f for f in os.listdir(path)
        if f.lower().endswith(".json") and os.path.isfile(os.path.join(path, f))
    }

def file_hash(path: str) -> str:
    """Gera hash SHA256 do conteúdo do arquivo"""
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

# ==========================================================
# EXECUÇÃO
# ==========================================================

def main():
    print("🔍 Lendo arquivos JSON em Videos...")
    videos_json = get_json_filenames(VIDEOS_DIR)

    print(f"📁 Total encontrados em Videos: {len(videos_json)}")

    if not videos_json:
        print("⚠️ Nenhum JSON encontrado. Encerrando.")
        return

    deleted = 0
    not_found = 0
    different_content = 0

    mode = "NOME + CONTEÚDO" if CHECK_CONTENT else "APENAS NOME"
    print(f"\n🧹 Modo de verificação: {mode}\n")

    for filename in sorted(videos_json):
        video_file = os.path.join(VIDEOS_DIR, filename)
        processed_file = os.path.join(PROCESSED_DIR, filename)

        if not os.path.exists(processed_file):
            print(f"❌ Não encontrado em movies_processed: {filename}")
            not_found += 1
            continue

        if CHECK_CONTENT:
            video_hash = file_hash(video_file)
            processed_hash = file_hash(processed_file)

            if video_hash != processed_hash:
                print(f"⚠️ Conteúdo diferente (não excluído): {filename}")
                different_content += 1
                continue

        os.remove(processed_file)
        print(f"🗑️ Excluído: {filename}")
        deleted += 1

    print("\n================ RESULTADO ================")
    print(f"✅ Excluídos: {deleted}")
    if CHECK_CONTENT:
        print(f"⚠️ Conteúdo diferente: {different_content}")
    print(f"❌ Não encontrados: {not_found}")
    print("==========================================")

if __name__ == "__main__":
    main()
