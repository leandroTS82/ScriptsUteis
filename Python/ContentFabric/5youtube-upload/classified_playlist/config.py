# config.py
import os

BASE_UPLOAD_DIR = r"C:\dev\scripts\ScriptsUteis\Python\ContentFabric\5youtube-upload"

SHARED_DIR = os.path.join(BASE_UPLOAD_DIR, "00_Shared")
CLASSIFIED_PLAYLIST_DIR = os.path.join(BASE_UPLOAD_DIR, "classified_playlist")

YOUTUBE_INVENTORY_JSON = os.path.join(
    SHARED_DIR,
    "youtube_uploaded_inventory.json"
)

EXPORT_SCRIPT = os.path.join(
    SHARED_DIR,
    "00_export_youtube_uploaded_inventory.py"
)

UPLOAD_METADATA_DIR = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\EnableToYoutubeUpload"

MOVIES_PROCESSED_DIR = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\movies_processed"

OUTPUT_DIR = os.path.join(CLASSIFIED_PLAYLIST_DIR, "output")

YOUTUBE_PLAYLIST_CONTEXT_JSON = os.path.join(
    OUTPUT_DIR,
    "youtube_playlist_context.json"
)

YOUTUBE_PLAYLIST_CLASSIFICATION_JSON = os.path.join(
    OUTPUT_DIR,
    "youtube_playlist_classification.json"
)

GROQ_MODEL = "llama-3.3-70b-versatile"
BATCH_SIZE = 25
MAX_RETRIES = 3
TIMEOUT_SECONDS = 60

PLAYLIST_PRIVACY_STATUS = "public"
DRY_RUN = False
SLEEP_SECONDS = 1.5