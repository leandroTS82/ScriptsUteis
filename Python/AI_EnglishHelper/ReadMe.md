# **DOCUMENTAÇÃO TÉCNICA – AI_EnglishHelper**

## **Sistema de Correção, Tradução e Geração de Conteúdo Didático com Groq + Gemini**

---

# **1. OBJETIVO DO SISTEMA**

O módulo **AI_EnglishHelper** foi projetado para:

1. Receber qualquer texto (palavra, frase, expressão) em português ou inglês.
2. Realizar:

   * Correção ortográfica (PT/EN)
   * Normalização gramatical (EN)
   * Tradução automática PT → EN
   * Ajustes de coerência semântica
3. Gerar conteúdo didático estruturado com:

   * Definição clara em português
   * Exemplos em inglês seguindo níveis CEFR (A1–C2)
   * Tamanhos configuráveis de frases (curta / média / longa)
4. Exibir um PREVIEW colorido no terminal para validação imediata.
5. Registrar:

   * A palavra/frase corrigida em **CreateLater.json**
   * O conteúdo didático completo em **TranscriptResults.json**
6. Usar IA de forma adaptativa:

   * **Groq** como modelo principal
   * **Gemini** como fallback automático
   * **Gemini** como opção forçada via flag `-Gemini`

---

# **2. ARQUITETURA DO SISTEMA**

```
AI_EnglishHelper
│
├── mainTranscript.py     ← Orquestrador principal
│
├── levels.json           ← Configura níveis e tamanhos de frases
│
├── CreateLater.json      ← Banco de pendências para estudo futuro
│
├── TranscriptResults.json← Banco de resultados didáticos gerados
│
├── ../Groq/groq_api_key.txt
└── ../Gemini/google-gemini-key.txt
```

---

# **3. FLUXO COMPLETO DO PROCESSO**

## **3.1 Entrada**

O usuário executa:

```
python mainTranscript.py "texto aqui"
python mainTranscript.py -Gemini "texto aqui"
```

---

## **3.2 Identificação do modo**

| Modo        | Comportamento                |
| ----------- | ---------------------------- |
| **Normal**  | Tenta Groq → fallback Gemini |
| **-Gemini** | Usa apenas Gemini            |

---

## **3.3 Correção/Tradução**

O sistema envia o texto para análise:

### **Tarefas realizadas pelos modelos:**

1. Detectar idioma (PT/EN)
2. Corrigir erros ortográficos
3. Corrigir erros gramaticais (EN)
4. Traduzir partes em português para inglês
5. Forçar saída sempre em inglês
6. Justificar erros caso existam

---

## **3.4 Sanitização**

Remove pontuação final e mantém somente a forma normalizada da expressão.

---

## **3.5 Registro em CreateLater.json**

### Formato:

```json
{
  "pending": [
    "expression without final punctuation"
  ]
}
```

Regras:

* Não duplica elementos
* Nunca adiciona ponto final
* Cria o arquivo caso não exista

---

## **3.6 Consulta ao levels.json**

Exemplo:

```json
{
  "A1": { "enabled": true, "size": "short" },
  "A2": { "enabled": true, "size": "short" },
  "B1": { "enabled": true, "size": "medium" },
  "B2": { "enabled": true, "size": "long" }
}
```

### Interpretação:

| Level      | Tamanho    | Faixa de Palavras |
| ---------- | ---------- | ----------------- |
| **short**  | simples    | 4–8 palavras      |
| **medium** | contextual | 10–16 palavras    |
| **long**   | elaborada  | 18–28 palavras    |

Essa configuração dirige a IA para gerar frases adequadas ao nível de proficiência.

---

## **3.7 Geração do conteúdo didático**

A IA devolve:

```json
{
  "definition_pt": "explicação clara e natural em português",
  "examples": [
    {
      "level": "A2",
      "size": "short",
      "phrase": "English example sentence using the phrase"
    }
  ]
}
```

Regras rígidas aplicadas:

* Todas as frases são **sentenças completas**
* Todas devem conter literalmente:
  **"{corrected_sentence}"**
* O tamanho da frase obedece *levels.json*
* A definição deve ser curta e natural, sem repetir a expressão no início

---

## **3.8 Registro em TranscriptResults.json**

Formato:

```json
[
  {
    "palavra_chave": "corrected sentence",
    "definicao_pt": "meaning",
    "exemplos": [
      { "level": "A2", "size": "short", "phrase": "..." }
    ]
  }
]
```

* Cresce indefinidamente como banco de conhecimento
* Ideal para alimentar Anki / banco de estudo

---

## **3.9 Exibição em PREVIEW**

O terminal exibe:

* Modelo utilizado (Groq/Gemini)
* Correção ortográfica
* Justificativa do erro
* Tradução final
* Definição clara em português
* Exemplos formatados por nível

Preview em alta legibilidade e com uso de cores ANSI.

---

# **4. LEVELS.JSON — COMO FUNCIONA**

O arquivo levels.json é o **coração pedagógico** do sistema.

### **Cada nível possui:**

* `"enabled"`: ativa ou desativa
* `"size"`: short / medium / long

### **Exemplos de uso:**

### Desabilitar níveis A1 e C2:

```json
{
  "A1": { "enabled": false, "size": "short" },
  "A2": { "enabled": true, "size": "short" },
  "B1": { "enabled": true, "size": "medium" },
  "B2": { "enabled": true, "size": "long" },
  "C1": { "enabled": false, "size": "long" },
  "C2": { "enabled": false, "size": "long" }
}
```

### Alterar comprimento das frases:

```json
"B1": { "enabled": true, "size": "long" }
```

---

# **5. COMO O MODELO AJUSTA O TAMANHO DAS FRASES**

O prompt instrui a IA:

| Tamanho | Instrução dada à IA                     | Palavras |
| ------- | --------------------------------------- | -------- |
| short   | "create a very short sentence"          | 4-8      |
| medium  | "create a medium-length sentence"       | 10–16    |
| long    | "create an expanded, detailed sentence" | 18–28    |

A IA então gera frases naturalíssimas dentro dessa janela.

---

# **6. INTEGRAÇÃO COM ANKI (RECURSO OPCIONAL)**

O sistema já está preparado para exportação ANKI porque:

* Cada entrada tem **palavra-chave**, **definição**, **exemplos**
* É fácil montar flashcards:

### **Frente (campo 1)**

```
corrected_sentence
```

### **Verso (campo 2)**

```
Definição PT:
{definicao_pt}

Exemplos:
(A2) ...
(B1) ...
(B2) ...
```

Se desejar, posso gerar:

* Exportação CSV pronta para Anki
* Exportação automática ao gerar o conteúdo
* Criação de decks separados por nível

---

# **7. TRATAMENTO DE ERROS**

| Tipo de erro      | Comportamento                        |
| ----------------- | ------------------------------------ |
| Groq indisponível | Fallback automático → Gemini         |
| Gemini falhar     | Mensagem clara e interrupção         |
| JSON malformado   | Correção automática delimitando `{}` |
| Entrada inválida  | Notificação no terminal              |

---

# **8. DECISÃO DE MODELO**

| Situação        | Modelo              |
| --------------- | ------------------- |
| Execução normal | Groq (1ª tentativa) |
| Groq falha      | Gemini              |
| Usuário força   | Gemini              |

Essa arquitetura reduz custo e tempo de resposta.

---

# **9. EXTENSÕES RECOMENDADAS (OPCIONAIS)**

Posso expandir o sistema para:

### 1. **Exportação ANKI automática**

JSON → CSV → Deck
Ou até **gerar .apkg** automaticamente.

### 2. **Geração de Áudio com TTS**

Perfeito para listening.

### 3. **Geração de imagens**

Ilustrações para cada palavra.

### 4. **Comparação EN→PT e PT→EN automática**

### 5. **Dashboard Web (Streamlit)**

Visualizar banco de estudos.

---

# **10. DIAGRAMA DE ALTO NÍVEL**

```
Entrada → Correção Ortográfica → Tradução EN → WordBank → Preview
    ↓             ↓                    ↓          ↓
CreateLater    Tratamento        TranscriptResults
```

---

# **11. Conclusão**

O AI_EnglishHelper agora é um sistema:

* Robusto
* Didático
* Extensível
* Controlado por níveis
* Híbrido Groq + Gemini
* Preparado para ANKI
* Utilizável tanto para frases quanto para expressões complexas

---

