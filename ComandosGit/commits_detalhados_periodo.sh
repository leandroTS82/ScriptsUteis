#!/bin/bash

# Script para listar commits detalhados de uma branch num período em meses e gerar CSV.

# Como usar:
# 1. Dê permissão de execução: chmod +x commits_detalhados_periodo.sh
# 2. Execute o script passando o nome da branch e o período em meses:
#    ./commits_detalhados_periodo.sh <nome_da_branch> <periodo_em_meses>
# Exemplo:
#    ./commits_detalhados_periodo.sh develop-iteris 3
# Isso vai gerar um arquivo CSV com commits da branch 'develop-iteris' dos últimos 3 meses.

BRANCH=$1
MESES=$2
OUTPUT_FILE="commits_${BRANCH}_ultimos_${MESES}_meses.csv"

# Validação de parâmetros
if [ -z "$BRANCH" ] || [ -z "$MESES" ]; then
  echo "Uso: ./commits_detalhados_periodo.sh <nome_da_branch> <periodo_em_meses>"
  exit 1
fi

# Atualiza referências remotas
git fetch origin

# Faz checkout da branch (ignora erro se já estiver nela)
git checkout $BRANCH 2>/dev/null

# Define data limite para filtro
SINCE_DATE=$(date -d "-$MESES months" +%Y-%m-%d)

# Cabeçalho do CSV
echo "Commit;Autor;Email;Data;Mensagem;Eh_Merge" > "$OUTPUT_FILE"

# Lista commits desde a data limite, formatando saída e identificando merges
git log $BRANCH --since="$SINCE_DATE" --pretty=format:"%H;%an;%ae;%ad;%s" --date=iso | while IFS=";" read HASH AUTOR EMAIL DATA MSG
do
  PARENTS=$(git rev-list --parents -n 1 $HASH)
  NUM_PARENTS=$(echo $PARENTS | wc -w)
  if [ "$NUM_PARENTS" -gt 2 ]; then
    EH_MERGE="SIM"
  else
    EH_MERGE="NAO"
  fi

  echo "$HASH;$AUTOR;$EMAIL;$DATA;$MSG;$EH_MERGE" >> "$OUTPUT_FILE"
done

echo "Arquivo gerado: $OUTPUT_FILE"
