Você deve gerar um conteúdo de estudo no formato JSON compatível com o script MakeMp3.py e MakeVideo.py.

O tema do conteúdo será indicado.

Siga exatamente a estrutura abaixo:

"repeat_each": { "pt": 1, "en": 2 }
"introducao" → frase curta de boas-vindas ao tema
"nome_arquivos" → nome simples e descritivo do tema
"Listening" → lista de blocos conforme o modelo:

1️⃣ Termo em inglês
{ "lang": "en", "text": "TERM", "pause": 300 },
2️⃣ Explicação curta em português (com instrução de prática)
{ "lang": "pt", "text": "Significa '...', breve explicação e 'A seguir, três frases para você praticar.'", "pause": 800},
3️⃣ Três frases em inglês com pausas curtas
{ "lang": "en", "text": "Frase 1", "pause": 800},
{ "lang": "en", "text": "Frase 2", "pause": 800},
{ "lang": "en", "text": "Frase 3", "pause": 800},
4️⃣ Mensagem de transição curta em português — natural e variada (ex:
“Vamos continuar.”, “Seguindo para a próxima.”, “Próxima palavra.”, “Vamos adiante.” etc.)
{ "lang": "pt", "text": "Mensagem de transição curta.", "pause": 400},
⚠️ O último item do "Listening" deve substituir essa transição por uma mensagem de encerramento curta, como:
“Parabéns! Você concluiu o treino.” ou “Muito bem, fim do conteúdo de hoje.”

🎯 O resultado deve ser coerente, didático e pronto para gerar áudio/vídeo de estudo.
Use exemplos simples e naturais, adequados para estudantes de inglês de nível básico a intermediário.

✅ Exemplo de uso
Tema: Prepositions of Place (in, on, under, next to, between)

Prompt:
“Use a estrutura memorizada de Listening e Pronunciation e gere o conteúdo sobre o tema: Prepositions of Place (in, on, under, next to, between).”

Aguarde proximas instruções.