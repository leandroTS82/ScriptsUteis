"""
=====================================================================
 Script: optimize_channel.py
 Autor: Leandro (com a ajuda do Gemini)
 Finalidade: 
   1. Baixa a lista de vídeos do seu canal.
   2. Envia os dados atuais (Título/Desc) para a Groq.
   3. A Groq reescreve usando as regras de Copywriting/SEO.
   4. Atualiza o vídeo no YouTube automaticamente.
=====================================================================
"""
import os
import json
import time
import requests
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

# --- CONFIGURAÇÕES ---
DRY_RUN = False  # <--- SE TRUE, NÃO ALTERA O YOUTUBE (Só imprime no console). MUDE PARA False PARA RODAR VALENDO.
MAX_VIDEOS = 50  # Quantos vídeos processar por vez (para poupar cota)
GROQ_MODEL = "openai/gpt-oss-20b" # Ou "llama3-70b-8192" se preferir

# Arquivos de Auth (Mesmos do seu script de upload)
TOKEN_PATH = "C:\\Users\\leand\\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\\LTS SP Site - Documentos de estudo de inglês\\FilesHelper\\secret_tokens_keys\\youtube_token.json"
CLIENT_SECRET_FILE = "C:\\Users\\leand\\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\\LTS SP Site - Documentos de estudo de inglês\\FilesHelper\\secret_tokens_keys\\youtube_token.json"
GROQ_API_KEY_FILE = "C:\\Users\\leand\\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\\LTS SP Site - Documentos de estudo de inglês\\FilesHelper\\secret_tokens_keys\\groq_api_key.txt"

# Prompts do Sistema (Reutilizando sua lógica vencedora)
SYSTEM_PROMPT = {
    "role": "system",
    "content": """
    You are a YouTube SEO Expert. Your task is to REWRITE existing metadata to improve CTR.
    ""
    INPUT: Old Title and Old Description.
    OUTPUT: A JSON object with 'title' (max 100 chars, clickbait-style but honest), 'description' (SEO optimized), and 'tags' (list).
    RULES:
    1. Keep the same video topic. Do not hallucinate new content.
    2. Titles must use the pattern: 'Portuguese Hook + English Topic'.
    3. Description must start with a question/hook.
    4. Return ONLY valid JSON.
    """
}

# Scopes necessários para LER e ATUALIZAR
SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]

def load_api_key():
    with open(GROQ_API_KEY_FILE, "r") as f:
        return f.read().strip()

def get_authenticated_service():
    creds = None
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "r") as token:
            creds = Credentials.from_authorized_user_info(json.load(token), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=8080)
        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())
    return build("youtube", "v3", credentials=creds)

# --- 1. FUNÇÃO: LISTAR VÍDEOS DO CANAL ---
def list_channel_videos(youtube):
    # Pega o ID da playlist de "Uploads" do canal
    channels_response = youtube.channels().list(mine=True, part="contentDetails").execute()
    uploads_playlist_id = channels_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    videos = []
    request = youtube.playlistItems().list(
        part="snippet,contentDetails",
        playlistId=uploads_playlist_id,
        maxResults=MAX_VIDEOS 
    )
    
    while request and len(videos) < MAX_VIDEOS:
        response = request.execute()
        for item in response["items"]:
            video_id = item["contentDetails"]["videoId"]
            # Precisamos pegar tags e categoria, que não vem no playlistItem
            vid_response = youtube.videos().list(part="snippet", id=video_id).execute()
            if not vid_response["items"]: continue
            
            snippet = vid_response["items"][0]["snippet"]
            videos.append({
                "id": video_id,
                "title": snippet["title"],
                "description": snippet["description"],
                "categoryId": snippet["categoryId"],
                "tags": snippet.get("tags", [])
            })
        
        request = youtube.playlistItems().list_next(request, response)
    
    return videos

# --- 2. FUNÇÃO: CHAMAR GROQ ---
def optimize_metadata_with_groq(video_data):
    api_key = load_api_key()
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    user_prompt = f"""
    Here is the CURRENT (BAD) metadata for a video about learning English:
    Title: {video_data['title']}
    Description: {video_data['description']}
    
    Please REWRITE this to make it viral and educational. 
    Category ID is {video_data['categoryId']}.
    Target Audience: Brazilians learning English.
    """

    payload = {
        "model": GROQ_MODEL,
        "messages": [SYSTEM_PROMPT, {"role": "user", "content": user_prompt}],
        "temperature": 0.3
    }

    try:
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"]
            # Limpeza básica caso a Groq mande markdown ```json
            content = content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        else:
            print(f"Erro Groq: {response.text}")
            return None
    except Exception as e:
        print(f"Erro Groq Exception: {e}")
        return None

# --- 3. FUNÇÃO: ATUALIZAR YOUTUBE ---
def update_youtube_video(youtube, video_id, new_metadata, old_category_id):
    if DRY_RUN:
        print(f"\n[DRY RUN] Simulação de Update para ID: {video_id}")
        print(f"NOVO TÍTULO: {new_metadata['title']}")
        print(f"NOVA DESC : {new_metadata['description'][:50]}...")
        return

    try:
        print(f"\n[REAL] Atualizando vídeo {video_id}...")
        youtube.videos().update(
            part="snippet",
            body={
                "id": video_id,
                "snippet": {
                    "title": new_metadata["title"],
                    "description": new_metadata["description"],
                    "tags": new_metadata.get("tags", []),
                    "categoryId": old_category_id # Mantém a categoria original ou muda se quiser
                }
            }
        ).execute()
        print("✅ Sucesso!")
    except Exception as e:
        print(f"❌ Falha ao atualizar: {e}")

# --- MAIN ---
if __name__ == "__main__":
    youtube = get_authenticated_service()
    
    print("📥 Baixando lista de vídeos...")
    my_videos = list_channel_videos(youtube)
    print(f"Encontrados {len(my_videos)} vídeos para processar.")

    for vid in my_videos:
        print(f"\n-------------------------------------------------")
        print(f"Processando: {vid['title']}")
        
        # 1. Gera novos dados
        new_data = optimize_metadata_with_groq(vid)
        
        if new_data:
            # 2. Atualiza (ou simula)
            update_youtube_video(youtube, vid['id'], new_data, vid['categoryId'])
        
        # Pausa para não estourar rate limit da Groq
        time.sleep(2)