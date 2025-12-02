# 📘 **groq_wordbank.py — Documentação Completa**

```md
# 📘 groq_wordbank.py — Documentação Completa

## 📌 Visão Geral

O script `groq_wordbank.py` automatiza a criação de **Word Banks** inteligentes usando a API da **Groq**.

Ele:
- Detecta idioma (PT/EN)
- Traduz automaticamente para inglês
- Suporta múltiplas palavras
- Aceita entrada em vários formatos (word, lista, JSON inline)
- Gera arquivos JSON seguindo um padrão estruturado
- Exibe um **preview visual e amigável no terminal**
- Pode gerar JSON **ou apenas exibir preview (-njson)**

---

# 🧩 Estrutura Geral

```

groq_wordbank.py
groq_api_key.txt
systemPrompt.json
userPromptBase.json
translator_prompt.json
2ContentToCreate/    → saída dos JSONs gerados

````

---

# 🚀 Como usar

## ✔ Execução normal (gera JSON + preview)

```bash
python groq_wordbank.py crowd
````

Entrada com múltiplas palavras:

```bash
python groq_wordbank.py "crowd, belong, sunset"
```

Lista JSON:

```bash
python groq_wordbank.py ["crowd","belong","sunset"]
```

Objeto:

```bash
python groq_wordbank.py {crowd}
```

---

# 🆕 Uso com `-njson` (somente preview)

O modo `-njson` **não salva** o arquivo JSON.
Ele apenas exibe o preview no terminal.

### Exemplos:

```bash
python groq_wordbank.py -njson crowd
```

```bash
python groq_wordbank.py -njson ["crowd","sunset"]
```

```bash
python groq_wordbank.py -njson {crowd}
```

```bash
python groq_wordbank.py -njson "phrasal verb"
```

---

# 🧠 Como funciona

## 1. **Detecção de formato da entrada**

A função:

```python
parse_words()
```

Permite que a entrada seja:

| Entrada           | Resultado        |
| ----------------- | ---------------- |
| `"word"`          | array com 1 word |
| `"word1, word2"`  | lista            |
| `["a","b","c"]`   | lista JSON real  |
| `{word}`          | word única       |
| `"duas palavras"` | word composta    |

---

## 2. **Tradução PT → EN**

Toda word é traduzida para inglês usando:

```python
translate_to_en()
```

Que envia a palavra ao modelo Groq com um prompt tradutor.

---

## 3. **Construção do prompt final**

São usados dois arquivos:

* `systemPrompt.json`
* `userPromptBase.json`

O script injeta:

```python
base_prompt["words"] = translated_words
```

E envia para o Groq.

---

## 4. **Geração do JSON final**

Se não estiver no modo `-njson`, o resultado é salvo em:

```
2ContentToCreate/nome_gerado.json
```

---

## 5. **Preview no Terminal (Visual melhorado)**

O preview usa:

* Cores ANSI (funciona no Windows 10+)
* Caixas de texto
* Emojis
* Destaque para:

  * introdução
  * nome_arquivos
  * grupos do WORD_BANK
  * exemplos
  * finalização

Exemplo visual:

```
╔════════════════════════════════════════════╗
║            PREVIEW DO WORD BANK           ║
╚════════════════════════════════════════════╝

📌 Introdução:
 ...

📁 nome_arquivos:
 ...

🧠 WORD BANK:

┌── Grupo 1 ─────────────────────┐
🇺🇸 Palavra-chave: crowd
📘 Definição PT: Significa...
   ➜ Exemplo EN: ...
⭐ Finalização PT: ...
└───────────────────────────────────────┘
```

---

# 📂 Saída dos arquivos JSON

O nome do arquivo segue regras:

### Apenas 1 palavra:

```
crowd.json
```

### Várias palavras:

```
Multiple_crowd_belong_sunset.json
```

### Lista agrupada:

```
Group_crowd_belong.json
```

---

# 📁 Estrutura do JSON gerado

Sempre segue esta estrutura:

```json
{
  "repeat_each": { "pt": 1, "en": 2 },
  "introducao": "... estilo youtuber ...",
  "nome_arquivos": "Tema_word",
  "WORD_BANK": [
    [
      { "lang": "en", "text": "crowd", "pause": 1000 },
      { "lang": "pt", "text": "Significa ..." },
      { "lang": "en", "text": "Example..." },
      { "lang": "pt", "text": "Finalização amigável" }
    ]
  ]
}
```

---

# 🔥 Recursos Internos

## ✔ Normalização do WordBank

Mesmo que o modelo retorne dados inconsistentes:

```python
normalize_wordbank()
```

Corrige automaticmente:

* texto solto → vira {lang,text}
* objetos inline → são convertidos
* strings JSON → são parseadas

---

## ✔ Agrupamento inteligente

Se o modelo retornar:

```
[{obj},{obj},{obj}]
```

É convertido para:

```
[[{obj},{obj},{obj}]]
```

---

# 🛠 Erros comuns e soluções

### ❗ "FileNotFoundError: systemPrompt.json"

Crie o arquivo na raiz:

```
./systemPrompt.json
```

### ❗ "Bearer token inválido"

Preencha:

```
groq_api_key.txt
```

com sua chave.

---

# 🧪 Exemplos avançados

### Gerar wordbank de 3 palavras com agrupamento automático:

```bash
python groq_wordbank.py ["run","jump","dance"]
```

### Executar apenas preview para testar o modelo:

```bash
python groq_wordbank.py -njson "time expressions"
```

---

# 🏁 Conclusão

Este script é uma ferramenta completa para:

✔ gerar wordbanks
✔ padronizar conteúdo
✔ criar treinos multilíngues
✔ trabalhar com vocabulário
✔ integrar com MakeVideo

Com o modo `-njson`, ficou ainda mais rápido para testar e ajustar.

---
