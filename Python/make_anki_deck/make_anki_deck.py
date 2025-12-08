import json
import genanki
import uuid
import os


# ============================================================
# CONFIGURAÇÃO DO DECK
# ============================================================

DECK_NAME = "English Learning - WordBank"
DECK_ID = int(uuid.uuid4().int >> 96)  # gera ID estável o suficiente
OUTPUT_FILE = "EnglishLearning.apkg"

# ============================================================
# CARREGAR SEU JSON
# ============================================================

JSON_FILE = r"C:\dev\scripts\ScriptsUteis\Python\AI_EnglishHelper\TranscriptResults.json"   # coloque aqui seu arquivo JSON completo

if not os.path.exists(JSON_FILE):
    raise FileNotFoundError(f"Arquivo {JSON_FILE} não encontrado!")

data = json.load(open(JSON_FILE, "r", encoding="utf-8"))

# ============================================================
# MODELOS DE CARTÕES (Anki templates)
# ============================================================

# Card 1 – Vocabulário → Definição
model_vocab = genanki.Model(
    int(uuid.uuid4().int >> 96),
    "Vocabulary Model",
    fields=[
        {"name": "Word"},
        {"name": "Definition"},
    ],
    templates=[
        {
            "name": "Card 1 - Word → Definition",
            "qfmt": "<h2>{{Word}}</h2>",
            "afmt": "<h2>{{Word}}</h2><hr><div>{{Definition}}</div>",
        }
    ]
)

# Card 2 – Palavra → Exemplos
model_examples = genanki.Model(
    int(uuid.uuid4().int >> 96),
    "Examples Model",
    fields=[
        {"name": "Word"},
        {"name": "Examples"},
    ],
    templates=[
        {
            "name": "Card 2 - Word → Examples",
            "qfmt": "<h2>{{Word}}</h2>",
            "afmt": "<h2>{{Word}}</h2><hr><div>{{Examples}}</div>",
        }
    ]
)

# Card 3 – Reverso (Definição → Palavra)
model_reverse = genanki.Model(
    int(uuid.uuid4().int >> 96),
    "Reverse Model",
    fields=[
        {"name": "Definition"},
        {"name": "Word"},
    ],
    templates=[
        {
            "name": "Card 3 - Definition → Word",
            "qfmt": "<h3>{{Definition}}</h3>",
            "afmt": "<h3>{{Definition}}</h3><hr><div>{{Word}}</div>",
        }
    ]
)

# ============================================================
# CRIAÇÃO DO DECK
# ============================================================

deck = genanki.Deck(DECK_ID, DECK_NAME)

def format_examples(ex_list):
    """ Converte a lista de exemplos em HTML para o cartão. """
    html = ""
    for item in ex_list:
        lvl = item["level"]
        phr = item["phrase"]
        html += f"<b>{lvl}</b>: {phr}<br>"
    return html


# ============================================================
# ADICIONAR NOTAS AO DECK
# ============================================================

for entry in data:
    palavra = entry["palavra_chave"]
    definicao = entry["definicao_pt"]
    exemplos = format_examples(entry["exemplos"])

    # Card 1 — Word → Definition
    note1 = genanki.Note(
        model=model_vocab,
        fields=[palavra, definicao]
    )
    deck.add_note(note1)

    # Card 2 — Word → Examples
    note2 = genanki.Note(
        model=model_examples,
        fields=[palavra, exemplos]
    )
    deck.add_note(note2)

    # Card 3 — Definition → Word
    note3 = genanki.Note(
        model=model_reverse,
        fields=[definicao, palavra]
    )
    deck.add_note(note3)


# ============================================================
# GERAR ARQUIVO APKG
# ============================================================

package = genanki.Package(deck)
package.write_to_file(OUTPUT_FILE)

print(f"Arquivo Anki gerado com sucesso: {OUTPUT_FILE}")
