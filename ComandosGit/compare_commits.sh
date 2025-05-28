#!/bin/bash

# Variáveis de entrada
BRANCH_ORIGEM=$1
BRANCH_DESTINO=$2
MESES=$3
OUTPUT_FILE="commits_comparacao.csv"

# Validação de argumentos
if [ -z "$BRANCH_ORIGEM" ] || [ -z "$BRANCH_DESTINO" ] || [ -z "$MESES" ]; then
  echo "Uso: ./compare_commits.sh <branch_origem> <branch_destino> <quantidade_meses>"
  exit 1
fi

# Atualiza branches (opcional)
git fetch

# Data limite
SINCE_DATE=$(date -d "-$MESES months" +%Y-%m-%d)

# Header do CSV
echo "Commit;Autor;Data;Mensagem;Presente_na_${BRANCH_DESTINO};Eh_Merge" > $OUTPUT_FILE

# Lista commits da branch origem desde a data limite
git log $BRANCH_ORIGEM --since="$SINCE_DATE" --pretty=format:"%H;%an;%ad;%s" --date=iso | while IFS=";" read HASH AUTOR DATA MSG
do
  # Verifica se o commit existe na branch destino
  if git branch --contains $HASH | grep -q "$BRANCH_DESTINO"; then
    PRESENTE="SIM"
  else
    PRESENTE="NAO"
  fi

  # Verifica se é um commit de merge (tem 2 ou mais pais)
  PARENTS=$(git rev-list --parents -n 1 $HASH)
  NUM_PARENTS=$(echo $PARENTS | wc -w)
  if [ "$NUM_PARENTS" -gt 2 ]; then
    EH_MERGE="SIM"
  else
    EH_MERGE="NAO"
  fi

  # Escreve no CSV
  echo "$HASH;$AUTOR;$DATA;$MSG;$PRESENTE;$EH_MERGE" >> $OUTPUT_FILE
done

echo "Arquivo gerado: $OUTPUT_FILE"
