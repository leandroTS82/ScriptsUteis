```md
# 🎬 **groq_MakeVideo — Automação completa para geração de metadata de vídeos**

Este script automatiza toda a criação de:

- **Título**
- **Descrição**
- **Tags**
- **Playlist**
- **Configurações de Publicação**
- **Thumbnail (opcional)**

Usando a API da **Groq**, com controle total via arquivo de configuração.

---

# 🚀 **Recursos principais**

- 🔄 Processamento automático de arquivos JSON complementares  
- 🧠 Combinação inteligente com arquivos de prompt-base  
- 🎥 Busca automática do vídeo associado pelo nome  
- 📝 Geração de JSON final com o mesmo nome do arquivo de vídeo  
- 🖼 Geração de thumbnail (ativável/desativável via config ou CLI)  
- ♻ Retry e backoff automático em caso de rate limit  
- 🔧 Toda a configuração centralizada em `groq_MakeVideo.json`  
- 🐛 Modo debug para análise detalhada  
- 📱 Compatível com Windows e Android (Termux)

---

# 📁 **Estrutura sugerida**

```

📦 C:\Content
├── Lesson1.mp4
├── info_Lesson1.json
├── Lesson2.mp4
├── vocabulary_Lesson2.json
├── ToGroq_info_Lesson1.json        ← já processado
├── metadata_Lesson1_20250110.json
├── Lesson1.jpg                     ← thumbnail gerada

````

---

# 🆕 **Modo Simplificado (apenas 1 path)**

Agora o script permite execução com **somente um argumento**.

Use este modo quando os **JSONs complementares** e os **vídeos** estão no mesmo diretório.

---

## ✔ **Uso**

```bash
python groq_MakeVideo.py "C:\Content"
````

### O script fará automaticamente:

* Ler os JSONs complementares de: `C:\Content`
* Buscar vídeos em: `C:\Content`
* Criar o JSON final em: `C:\Content`
* Renomear JSONs processados para:
  `ToGroq_<nome>.json`

---

## ✔ **Comportamento automático**

| Argumentos recebidos | json_dir | video_dir |
| -------------------- | -------- | --------- |
| **1 argumento**      | path     | path      |
| **2 argumentos**     | arg1     | arg2      |

---

# 📌 **Exemplos práticos**

### 🔹 **Modo automático (1 argumento)**

```bash
python groq_MakeVideo.py "D:\Projetos\Ingles\Lesson05"
```

### 🔹 **Modo tradicional (2 argumentos)**

```bash
python groq_MakeVideo.py "D:\JSONs" "D:\Videos"
```

