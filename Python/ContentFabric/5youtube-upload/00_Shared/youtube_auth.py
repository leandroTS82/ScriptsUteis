from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

import os

TOKEN_PATH = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Base\FilesHelper\secret_tokens_keys\youtube_token.json"

CLIENT_SECRET_FILE = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Base\FilesHelper\secret_tokens_keys\youtube-upload-desktop.json"

SCOPES = [
    "https://www.googleapis.com/auth/youtube"
]


def get_youtube_client():
    creds = None

    # ---------------------------------------------------------
    # CARREGA TOKEN EXISTENTE
    # ---------------------------------------------------------
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(
            TOKEN_PATH,
            SCOPES
        )

    # ---------------------------------------------------------
    # REFRESH TOKEN AUTOMÁTICO
    # ---------------------------------------------------------
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())

            with open(TOKEN_PATH, "w", encoding="utf-8") as token:
                token.write(creds.to_json())

            print("Token renovado automaticamente.")

        except Exception as e:
            print(f"Erro ao renovar token: {e}")
            creds = None

    # ---------------------------------------------------------
    # NOVA AUTENTICAÇÃO
    # ---------------------------------------------------------
    if not creds or not creds.valid:

        flow = InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRET_FILE,
            SCOPES
        )

        creds = flow.run_local_server(
            host="localhost",
            port=8080,
            open_browser=True
        )

        with open(TOKEN_PATH, "w", encoding="utf-8") as token:
            token.write(creds.to_json())

        print("Novo token salvo.")

    return build(
        "youtube",
        "v3",
        credentials=creds
    )