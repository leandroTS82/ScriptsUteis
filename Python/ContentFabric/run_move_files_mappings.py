# =============================================================================
# CONFIGURAÇÕES
# =============================================================================

from pathlib import Path
import shutil

# -------------------------------------------------------------------------
# Caminhos de origem e destino
# Defina quantos pares quiser
# -------------------------------------------------------------------------

PATH_MAPPINGS = [
    {
        # Vídeos
        "source": Path(r"C:\dev\scripts\ScriptsUteis\Python\Gemini\MakeVideoGemini\outputs\videos"),
        "destination": Path(r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\Videos"),
    },
    {
        # Áudio
        "source": Path(r"C:\dev\scripts\ScriptsUteis\Python\Gemini\MakeVideoGemini\outputs\audio"),
        "destination": Path(r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Audios para estudar inglês"),
    },
    {
        # Imagens
        "source": Path(r"C:\dev\scripts\ScriptsUteis\Python\Gemini\MakeVideoGemini\outputs\images"),
        "destination": Path(r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\Images"),
    },
    {
        # Áudio história
        "source": Path(r"C:\dev\scripts\ScriptsUteis\Python\Gemini\MakeHistorieMovie\outputs\audio"),
        "destination": Path(r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Audios para estudar inglês\Histories"),
    },
    {
        # Imagens história
        "source": Path(r"C:\dev\scripts\ScriptsUteis\Python\Gemini\MakeHistorieMovie\outputs\images"),
        "destination": Path(r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\Images"),
    },
    {
        # Vídeos história
        "source": Path(r"C:\dev\scripts\ScriptsUteis\Python\Gemini\MakeHistorieMovie\outputs\videos"),
        "destination": Path(r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\Histories"),
    },
]

# -------------------------------------------------------------------------
# Filtros (OR lógico – se atender a qualquer critério, passa)
# Deixe vazio ("") para desativar
# -------------------------------------------------------------------------

STARTS_WITH = ""     # arquivos que INICIAM com
CONTAINS    = ""     # arquivos que CONTÊM
EXACT_NAME  = ""     # nome EXATO
EXTENSION   = ""     # extensão (ex: ".mp3")

# -------------------------------------------------------------------------
# Flags de controle
# -------------------------------------------------------------------------

INCLUDE_SUBFOLDERS = True     # True = percorre subpastas
DRY_RUN            = False    # True = apenas preview
PREVIEW_SAMPLE     = 10       # Quantos arquivos mostrar no preview


# =============================================================================
# FUNÇÕES
# =============================================================================

def match_filters(file_path: Path) -> bool:
    """
    Replica exatamente a lógica do PowerShell:
    - Case-insensitive
    - OR lógico entre filtros
    - Se todos os filtros estiverem vazios, aceita tudo
    """
    name = file_path.name
    ext  = file_path.suffix

    if not any([STARTS_WITH, CONTAINS, EXACT_NAME, EXTENSION]):
        return True

    return (
        (STARTS_WITH and name.lower().startswith(STARTS_WITH.lower())) or
        (CONTAINS and CONTAINS.lower() in name.lower()) or
        (EXACT_NAME and name.lower() == EXACT_NAME.lower()) or
        (EXTENSION and ext.lower() == EXTENSION.lower())
    )


def list_files(source: Path):
    if INCLUDE_SUBFOLDERS:
        return [f for f in source.rglob("*") if f.is_file()]
    return [f for f in source.glob("*") if f.is_file()]


# =============================================================================
# EXECUÇÃO
# =============================================================================

for mapping in PATH_MAPPINGS:

    source = mapping.get("source")
    destination = mapping.get("destination")

    if not source or not destination:
        continue

    # ---------------------------------------------------------------------
    # Validar origem
    # ---------------------------------------------------------------------
    if not source.exists():
        print("\nOrigem não encontrada. Ignorando:")
        print(f"  {source}")
        continue

    # ---------------------------------------------------------------------
    # Garantir destino
    # ---------------------------------------------------------------------
    destination.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------------------
    # Listar arquivos
    # ---------------------------------------------------------------------
    files = list_files(source)
    filtered = [f for f in files if match_filters(f)]

    # ---------------------------------------------------------------------
    # Preview / Execução
    # ---------------------------------------------------------------------
    if DRY_RUN:
        print("\n================ PREVIEW =================")
        print(f"Origem:   {source}")
        print(f"Destino: {destination}")
        print("")
        print(f"Total encontrados: {len(files)}")
        print(f"Total a mover:     {len(filtered)}")
        print("")

        if filtered:
            print("Exemplos:")
            for f in filtered[:PREVIEW_SAMPLE]:
                print(f" - {f.name}")

            if len(filtered) > PREVIEW_SAMPLE:
                print(f" ... e mais {len(filtered) - PREVIEW_SAMPLE}")
        else:
            print("Nenhum arquivo corresponde aos filtros.")

        print("==========================================")
        print("Modo PREVIEW ativo. Nenhum arquivo movido.")

    else:
        for file in filtered:
            target = destination / file.name
            shutil.move(str(file), str(target))

        print("\nProcesso concluído.")
        print(f"Arquivos movidos: {len(filtered)}")