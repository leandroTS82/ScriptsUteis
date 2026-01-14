============================================================
 Script: video_slicer.py
 Autor: Leandro
 Descrição:
   - Faz slices de um vídeo com base em horários HH:mm
   - Aceita 1 ou N horários
       * 1 horário  → gera 2 vídeos (antes / depois)
       * N horários → slices consecutivos
   - Pode ser usado:
       1) Via CLI
       2) Via variáveis internas
   - Salva os cortes na pasta atual (./)
   
O comportamento é o seguinte:
    Se parâmetros CLI forem informados, eles têm prioridade
    Se nenhum parâmetro CLI for informado, o script usa as variáveis configuráveis no topo
    O código continua único, limpo e previsível (sem duplicações)
============================================================

USO VIA CLI:
python video_slicer.py \
  --video-path "C:\\Videos" \
  --video-name "aula.mp4" \
  --times "00:00,02:30,05:00,07:15"

USO VIA VARIÁVEIS (SEM CLI):
python video_slicer.py
============================================================

============================================================
 Script: video_slicer.py
 Autor: Leandro
 Descrição:
   - Faz slices de um vídeo com base em offsets de tempo
   - Formatos aceitos:
       * MM:SS
       * HH:MM:SS
   - 1 tempo → gera 2 vídeos (antes / depois)
   - N tempos → slices consecutivos
   - Pode ser usado:
       1) Via CLI
       2) Via variáveis internas
============================================================