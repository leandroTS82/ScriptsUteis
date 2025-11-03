"""
===============================================================
 Script: MakeMp3.py
 Autor: Leandro
===============================================================

📌 O que este script faz?
---------------------------------------------------------------
Este script gera áudios MP3 a partir de frases definidas em um arquivo
JSON, utilizando o Google Text-to-Speech (gTTS) para síntese de voz
e o pydub para manipulação/concatenação de trechos.

Funcionalidades principais:
- Conversão de frases em múltiplos idiomas para áudio MP3.
- Diferentes modos de saída:
  - "separado" → arquivos separados por seção/tempo.
  - "juntos"   → único arquivo consolidado com todas as seções.
  - "ambos"    → gera tanto separados quanto o consolidado.
  - "frases"   → gera cada frase individualmente.
- Suporte a múltiplos idiomas (pt, en, es, fr).
- Velocidade configurável por idioma (nível 1 a 5).
- Controle de repetições por idioma ou frase individual.
- Pausas configuráveis entre idiomas e entre repetições.
- Labels (introdução de idioma antes da frase).
- Mensagens de introdução/anúncio por seção.
- Suporte a seção especial “Instrucoesadicionais”.
- Configuração opcional para personalizar nomes de arquivos.
- Suporte a velocidade por linha via chave `"VoiceSpeed"`.
    exemplo: { "lang": "en", "text": "This is a fast line.", "VoiceSpeed": 4 }

---------------------------------------------------------------
⚙️ Requisitos
---------------------------------------------------------------
- Python 3.9+
- Dependências Python:
    pip install gTTS pydub

---------------------------------------------------------------
📂 Estrutura esperada
---------------------------------------------------------------
- Arquivo de entrada:
    textos.json → contém frases e configurações
- Estrutura de saída:
    audios/<timestamp>/
        ├── separados/  (arquivos por tempo/seção)
        ├── juntos/     (arquivo consolidado)
        └── frases/     (quando output_mode = "frases")

---------------------------------------------------------------
📄 Exemplo de JSON (textos.json)
---------------------------------------------------------------
{
  "velocidades": { "pt": 3, "en": 2 },
  "repeat_each": { "pt": 2, "en": 1 },
  "introducao": "Bem-vindo ao estudo de idiomas!",
  "nome_arquivos": "EstudoIdiomas",
  "Presente": [
    { "lang": "pt", "text": "Eu estudo inglês.", "repeat": 2 },
    { "lang": "en", "text": "I study English." }
  ],
  "Passado": [
    [
      { "lang": "pt", "text": "Eu estudei inglês." },
      { "lang": "en", "text": "I studied English.", "pause": 500 }
    ]
  ],
  "Instrucoesadicionais": [
    { "lang": "pt", "text": "Repita estas frases diariamente." }
  ]
}

---------------------------------------------------------------
▶️ Como executar
---------------------------------------------------------------
1. Crie um arquivo textos.json no mesmo diretório do script.
2. Ajuste as configurações iniciais no script (output_mode, default_voiceSpeed).
3. Execute:
    python MakeMp3.py
4. Os arquivos serão gerados em:
    audios/<data_hora_execucao>/

---------------------------------------------------------------
📂 Saídas esperadas
---------------------------------------------------------------
- separados/ → um arquivo MP3 para cada tempo/seção.
- juntos/    → um único arquivo MP3 consolidado com todas as seções.
- frases/    → áudios separados por frase (caso configurado).
- nomes de arquivos podem ser personalizados pela config "nome_arquivos".

---------------------------------------------------------------
💡 Casos de uso
---------------------------------------------------------------
- Criação de materiais de estudo de idiomas com repetição controlada.
- Geração de áudios para prática de listening em múltiplos idiomas.
- Criação de playlists de frases com labels e pausas didáticas.
- Treinamento auditivo progressivo (seções por tempo verbal).
- Preparação de áudios customizados para cursos e workshops.

===============================================================
"""


import os
import json
from gtts import gTTS
from pydub import AudioSegment
from datetime import datetime

# =========================================================
# Configurações padrão
# =========================================================

output_mode = "juntos"  # "separado", "juntos", "ambos", "frases"

default_voiceSpeed = {
    "pt": 3, "en": 1, "es": 2, "fr": 2
}

default_config = {
    "repeat_each": { "pt": 1, "en": 1, "es": 1, "fr": 1 },
    "pausa_entre_idiomas": 800,
    "usar_labels": False,
    "introducao": "Olá, vamos iniciar nosso estudo do inglês?",
    "anunciar_tempo": True,
    "pausa_repeticao": 400,
    "nome_arquivos": None
}

labels = {
    "pt": "Português", "en": "English",
    "es": "Español", "fr": "Français"
}

section_labels = {
    "Instrucoesadicionais": "Instruções adicionais para estudo"
}

# =========================================================
# Funções auxiliares
# =========================================================

def setVoiceSpeed(audio, nivel: int) -> AudioSegment:
    if nivel <= 1:
        return audio
    elif nivel == 2:
        return audio
    else:
        fator = 1.0 + (nivel - 2) * 0.25
        return audio.speedup(playback_speed=fator)

def build_tts(text: str, lang: str, velocidade: int, temp_file: str) -> AudioSegment | None:
    if not text.strip():
        return None
    use_slow = velocidade == 1
    tts = gTTS(text=text, lang=lang, slow=use_slow)
    tts.save(temp_file)
    audio = AudioSegment.from_mp3(temp_file)
    return setVoiceSpeed(audio, velocidade)

def build_label(lang: str, output_dir: str, tempo: str, idx: str) -> AudioSegment | None:
    label_text = labels.get(lang)
    if not label_text:
        return None
    temp_file = os.path.join(output_dir, f"tmp_label_{tempo}_{idx}.mp3")
    gTTS(text=label_text, lang=lang, slow=False).save(temp_file)
    return AudioSegment.from_mp3(temp_file)

def generate_intro(text: str, output_dir: str, nome: str) -> AudioSegment:
    temp_file = os.path.join(output_dir, f"tmp_anuncio_{nome}.mp3")
    gTTS(text=text, lang="pt", slow=False).save(temp_file)
    return AudioSegment.from_mp3(temp_file)

def tempClear(output_dir: str):
    for f in os.listdir(output_dir):
        if f.startswith("tmp_") and f.endswith(".mp3"):
            try:
                os.remove(os.path.join(output_dir, f))
            except:
                pass

def check_lang(item) -> str:
    if isinstance(item, dict) and "lang" in item:
        return item["lang"]
    elif isinstance(item, list) and len(item) > 0 and "lang" in item[0]:
        return item[0]["lang"]
    return "pt"

# =========================================================
# Processamento principal de blocos
# =========================================================

def processar_bloco(frases, tempo: str, base_dir: str, config_estudo: dict, velocidades: dict) -> list:
    partes = []

    for idx, item in enumerate(frases, start=1):
        bloco = []

        # Pausa simples
        if isinstance(item, dict) and "pause" in item and "lang" not in item:
            bloco.append(AudioSegment.silent(duration=item["pause"]))

        # Frase mista (lista de trechos)
        elif isinstance(item, list):
            subpartes = []
            for sub_idx, trecho in enumerate(item, start=1):
                if "pause" in trecho and "text" not in trecho:
                    subpartes.append(AudioSegment.silent(duration=trecho["pause"]))
                else:
                    lang = trecho["lang"]
                    text = trecho.get("text", "").strip()
                    if not text:
                        continue

                    # 🆕 Suporte a VoiceSpeed
                    velocidade = trecho.get("VoiceSpeed", velocidades.get(lang, 2))

                    temp_file = os.path.join(base_dir, f"tmp_{tempo}_{idx}_{sub_idx}.mp3")

                    if config_estudo.get("usar_labels", False):
                        label_audio = build_label(lang, base_dir, tempo, f"{idx}_{sub_idx}")
                        if label_audio:
                            subpartes.append(label_audio)

                    audio = build_tts(text, lang, velocidade, temp_file)
                    if not audio:
                        continue

                    rep = trecho.get("repeat", config_estudo.get("repeat_each", {}).get(lang, 1))
                    for r in range(rep):
                        subpartes.append(audio)
                        if rep > 1 and r < rep - 1:
                            subpartes.append(AudioSegment.silent(duration=config_estudo.get("pausa_repeticao", 400)))

                    if "pause" in trecho:
                        subpartes.append(AudioSegment.silent(duration=trecho["pause"]))

            bloco.append(sum(subpartes))

        # Frase simples
        elif isinstance(item, dict) and "lang" in item and "text" in item:
            lang = item["lang"]
            text = item.get("text", "").strip()
            if not text:
                continue

            # 🆕 Suporte a VoiceSpeed
            velocidade = item.get("VoiceSpeed", velocidades.get(lang, 2))

            temp_file = os.path.join(base_dir, f"tmp_{tempo}_{idx}.mp3")

            if config_estudo.get("usar_labels", False):
                label_audio = build_label(lang, base_dir, tempo, idx)
                if label_audio:
                    bloco.append(label_audio)

            audio = build_tts(text, lang, velocidade, temp_file)
            if not audio:
                continue

            rep = item.get("repeat", config_estudo.get("repeat_each", {}).get(lang, 1))
            for r in range(rep):
                bloco.append(audio)
                if rep > 1 and r < rep - 1:
                    bloco.append(AudioSegment.silent(duration=config_estudo.get("pausa_repeticao", 400)))

            if "pause" in item:
                bloco.append(AudioSegment.silent(duration=item["pause"]))

        else:
            continue

        partes.append(sum(bloco))

        if config_estudo.get("pausa_entre_idiomas") and idx < len(frases):
            partes.append(AudioSegment.silent(duration=config_estudo["pausa_entre_idiomas"]))

    return partes

# =========================================================
# Execução principal
# =========================================================

try:
    with open("textos.json", "r", encoding="utf-8") as f:
        conteudo = json.load(f)
except Exception as e:
    print(f"Erro ao carregar JSON: {e}")
    exit(1)

config_estudo = default_config.copy()
velocidades = default_voiceSpeed.copy()

if "velocidades" in conteudo:
    velocidades.update(conteudo["velocidades"])
if "repeat_each" in conteudo:
    config_estudo["repeat_each"].update(conteudo["repeat_each"])
if "introducao" in conteudo:
    config_estudo["introducao"] = conteudo["introducao"]
if "nome_arquivos" in conteudo:
    config_estudo["nome_arquivos"] = conteudo["nome_arquivos"]

# Criar pastas
timestamp = datetime.now().strftime("%Y%m%d%H%M")
base_dir = os.path.join("audios")
separados_dir = os.path.join(base_dir, "separados")
juntos_dir = os.path.join(base_dir, "juntos")
frases_dir = os.path.join(base_dir, "frases")

if output_mode in ("separado", "ambos"):
    os.makedirs(separados_dir, exist_ok=True)
if output_mode in ("juntos", "ambos"):
    os.makedirs(juntos_dir, exist_ok=True)
if output_mode == "frases":
    os.makedirs(frases_dir, exist_ok=True)

todos_tempos = []

# Introdução
introducao_audio = None
if config_estudo.get("introducao"):
    introducao_audio = generate_intro(config_estudo["introducao"], base_dir, "intro")

# Seções
secoes = []
if "Instrucoesadicionais" in conteudo:
    secoes.append(("Instrucoesadicionais", conteudo["Instrucoesadicionais"]))
for tempo, frases in conteudo.items():
    if tempo in ("introducao", "Instrucoesadicionais", "velocidades", "repeat_each", "nome_arquivos"):
        continue
    secoes.append((tempo, frases))

# Processar
for tempo, frases in secoes:
    print(f"Gerando áudio para: {tempo}...")

    partes = []

    if config_estudo.get("anunciar_tempo", False):
        nome_amigavel = section_labels.get(tempo, tempo)
        anuncio_audio = generate_intro(f"Iniciando: {nome_amigavel}", base_dir, tempo)
        partes.append(anuncio_audio)

    partes.extend(processar_bloco(frases, tempo, base_dir, config_estudo, velocidades))

    if partes:
        combinado = sum(partes)

        if output_mode in ("separado", "ambos"):
            prefixo = config_estudo.get("nome_arquivos") or tempo
            final_file = os.path.join(separados_dir, f"{prefixo}_{tempo}.mp3")
            combinado.export(final_file, format="mp3")
            print(f"Arquivo gerado: {final_file}")

        if output_mode in ("juntos", "ambos"):
            todos_tempos.append(combinado)

    tempClear(base_dir)

# Consolidado
if output_mode in ("juntos", "ambos") and todos_tempos:
    combinado_total = sum(todos_tempos)
    if introducao_audio:
        combinado_total = introducao_audio + combinado_total
    prefixo = config_estudo.get("nome_arquivos") or "TodosTemposVerbais_VozGoogle"
    final_all = os.path.join(juntos_dir, f"{prefixo}.mp3")
    combinado_total.export(final_all, format="mp3")
    print(f"Arquivo final: {final_all}")

print("✅ Concluído! Arquivos salvos em:", base_dir)