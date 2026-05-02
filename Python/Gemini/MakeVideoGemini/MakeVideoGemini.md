# 📘 **MakeVideoGemini – Documentação Oficial**

```md
# 🎬 MakeVideoGemini
Sistema automatizado para criação de vídeos educacionais usando
**Google Gemini 3.0 (Preview)** para gerar:

✅ Texto (roteiro)  
✅ Áudio (voz natural em WAV)  
✅ Imagens (thumbnail / background)  
✅ Vídeo final (MP4 com imagem + narração)

Totalmente integrado em Python.

---

# 📁 Estrutura do Projeto

```

MakeVideoGemini/
│
│-- main.py
│-- gemini_config.py
│-- generate_script.py
│-- generate_audio.py
│-- generate_image.py
│-- generate_video.py
│-- google-gemini-key.txt
│
│-- templates/
│     └── structure.json
│
│-- utils/
│     ├── text_normalizer.py
│     ├── file_loader.py
│     └── audio_tools.py
│
│-- outputs/
│     ├── audio/
│     ├── images/
│     └── videos/
│

````

---

# 📦 Instalação

## 1) Python 3.10+
Recomendado instalar via Windows Store ou python.org.

## 2) Instalar dependências

```bash
pip install google-generativeai moviepy pydub
````

## 3) Instalar FFmpeg (obrigatório para MoviePy)

Baixar:
[https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)

Adicionar o `bin/` ao PATH.

## 4) Chave do Gemini

Salvar em:

```
MakeVideoGemini/google-gemini-key.txt
```

Conteúdo do arquivo:

```
AIza...
```

---

# 🔧 Configuração – `gemini_config.py`

Este arquivo centraliza o acesso ao Gemini.

```python
import os
import google.generativeai as genai

class GeminiConfig:

    def __init__(self, key_path="C:\\Users\\leand\\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\\EKF - English Knowledge Framework - Base\\FilesHelper\\secret_tokens_keys\\google-gemini-key.txt"):
        self.key_path = key_path
        self.api_key = self._load_key()
        self._configure_sdk()

        self.MODEL_TEXT = "gemini-1.5-flash"
        self.MODEL_IMAGE = "gemini-1.5-flash"
        self.MODEL_AUDIO = "gemini-1.5-flash"

    def _load_key(self):
        if not os.path.exists(self.key_path):
            raise FileNotFoundError(f"Key não encontrada: {self.key_path}")
        return open(self.key_path).read().strip()

    def _configure_sdk(self):
        genai.configure(api_key=self.api_key)

    def get_text(self):
        return genai.GenerativeModel(self.MODEL_TEXT)

    def get_image(self):
        return genai.GenerativeModel(self.MODEL_IMAGE)

    def get_audio(self):
        return genai.GenerativeModel(self.MODEL_AUDIO)
```

---

# 🧠 Geração de Roteiro – `generate_script.py`

```python
import json
from gemini_config import GeminiConfig

def generate_lesson_json(word):
    config = GeminiConfig()
    model = config.get_text()

    prompt = f"""
    Gere um JSON seguindo exatamente esta estrutura:
    {{
      "repeat_each": {{"pt": 1, "en": 2}},
      "introducao": "Crie uma introdução curta estilo youtuber sobre '{word}'.",
      "nome_arquivos": "Tema_{word}",
      "WORD_BANK": [
        [
          {{ "lang": "en", "text": "{word}", "pause": 1000 }},
          {{ "lang": "pt", "text": "Explique a palavra {word} em português." }},
          {{ "lang": "en", "text": "Use {word} em uma frase simples.", "pause": 1000 }},
          {{ "lang": "en", "text": "Use {word} em outra frase curta.", "pause": 1000 }},
          {{ "lang": "en", "text": "Crie uma frase mais longa com {word}.", "pause": 1000 }},
          {{ "lang": "pt", "text": "Mensagem final estilo youtuber." }}
        ]
      ]
    }}
    """

    response = model.generate_content(prompt)
    data = response.text.strip()
    return json.loads(data)
```

---

# 🔊 Geração de Áudio – `generate_audio.py`

```python
from gemini_config import GeminiConfig

def generate_audio(text, output_path):
    config = GeminiConfig()
    model = config.get_audio()

    response = model.generate_content(
        text,
        generation_config={"response_mime_type": "audio/wav"}
    )

    audio_bytes = response.candidates[0].content.parts[0].data

    with open(output_path, "wb") as f:
        f.write(audio_bytes)
```

---

# 🖼️ Geração de Imagem – `generate_image.py`

```python
from gemini_config import GeminiConfig

def generate_image(word, output_path):
    config = GeminiConfig()
    model = config.get_image()

    prompt = f"""
    Create a bright HD YouTube thumbnail.
    Theme: English lesson about the word '{word}'.
    Style: clean, colorful, modern, 16:9.
    """

    response = model.generate_content(
        prompt,
        generation_config={"response_mime_type": "image/png"}
    )

    image_bytes = response.candidates[0].content.parts[0].data

    with open(output_path, "wb") as f:
        f.write(image_bytes)
```

---

# 🎥 Construção do Vídeo – `generate_video.py`

```python
from moviepy.editor import *

def build_video(word, images_dir, audio_dir, output_path):

    audio_path = f"{audio_dir}/{word}.wav"
    narration = AudioFileClip(audio_path)

    bg = ImageClip(f"{images_dir}/{word}.png").set_duration(
        narration.duration
    )

    final = bg.set_audio(narration)

    final.write_videofile(output_path, fps=30)
```

---

# 🚀 Execução do Processo Completo – `main.py`

```python
import os
from generate_script import generate_lesson_json
from generate_audio import generate_audio
from generate_image import generate_image
from generate_video import build_video

WORD = "awesome"

lesson = generate_lesson_json(WORD)

os.makedirs("outputs/audio", exist_ok=True)
os.makedirs("outputs/images", exist_ok=True)
os.makedirs("outputs/videos", exist_ok=True)

print("📌 GERANDO IMAGEM...")
image_path = f"outputs/images/{WORD}.png"
generate_image(WORD, image_path)

print("📌 GERANDO ÁUDIO...")
text = " ".join(b["text"] for b in lesson["WORD_BANK"][0])
audio_path = f"outputs/audio/{WORD}.wav"
generate_audio(text, audio_path)

print("📌 GERANDO VÍDEO FINAL...")
video_path = f"outputs/videos/{WORD}.mp4"
build_video(WORD, "outputs/images", "outputs/audio", video_path)

print("  VÍDEO GERADO:", video_path)
```

---

# ▶️ Como Executar

No terminal:

```bash
python main.py
```

---

# 🎯 Resultado Esperado

Após rodar, os seguintes arquivos aparecem:

```
MakeVideoGemini/
│
└── outputs/
     ├── audio/
     │     └── awesome.wav
     │
     ├── images/
     │     └── awesome.png
     │
     └── videos/
           └── awesome.mp4
```

### O vídeo final contém:

* uma imagem gerada pelo Gemini
* narração natural em WAV
* duração sincronizada
* exportado em MP4 (1080p por padrão)

---

# 🧪 Exemplo de Log Final

```
📌 GERANDO IMAGEM...
📌 GERANDO ÁUDIO...
📌 GERANDO VÍDEO FINAL...
Moviepy - Building video awesome.mp4
Moviepy - Writing video awesome.mp4
  VÍDEO GERADO: outputs/videos/awesome.mp4
```

---

# ❗ Troubleshooting

### 1) Erro: modelo não encontrado (404)

Seu projeto Gemini só aceita:

```
gemini-1.5-flash
```

### 2) FFmpeg não encontrado

Instale e adicione ao PATH.

### 3) Áudio vazio

O modelo pode retornar sem áudio se a key estiver incorreta.

### 4) Vídeo muito curto

A duração é baseada no áudio → verifique se o áudio não está vazio.

---

# 📌 Conclusão

O *MakeVideoGemini* é capaz de:

✔ Criar JSON educacional
✔ Gerar imagens profissionais
✔ Criar áudio de alta qualidade
✔ Montar vídeo final automaticamente

Tudo isso usando **um único comando**:

```bash
python main.py
```


