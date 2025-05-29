#!/bin/bash

#===================================================================================
# Script: compare_commits.sh
# 
# Descrição:
#   Script para comparar commits entre duas branches do Git e gerar um relatório CSV
#   com informações detalhadas sobre cada commit, incluindo se está presente na branch
#   de destino e se é um commit de merge.
#
# Uso:
#   ./compare_commits.sh <branch_origem> <branch_destino> <quantidade_meses> <caminho_projeto> <caminho_saida>
#
# Parâmetros:
#   branch_origem    - Branch de origem para comparação
#   branch_destino   - Branch de destino para comparação
#   quantidade_meses - Quantidade de meses para analisar commits
#   caminho_projeto  - Caminho do repositório Git
#   caminho_saida    - Caminho onde o arquivo CSV será gerado
#
# Exemplo de execução:
#   ./compare_commits.sh develop main 3 /path/to/project /path/to/output
#   ./compare_commits.sh release master 2 C:\Dev\web-portal D:\Reports
#
# Saída:
#   Gera um arquivo CSV com as colunas:
#   - Commit (hash)
#   - Autor
#   - Data
#   - Mensagem
#   - Presente na branch destino
#   - É commit de merge
#===================================================================================

# Variáveis de entrada
BRANCH_ORIGEM=$1
BRANCH_DESTINO=$2
MESES=$3
PROJECT_PATH=$4
OUTPUT_PATH=$5

# Validação de argumentos
if [ -z "$BRANCH_ORIGEM" ] || [ -z "$BRANCH_DESTINO" ] || [ -z "$MESES" ] || [ -z "$PROJECT_PATH" ] || [ -z "$OUTPUT_PATH" ]; then
  echo "Uso: ./compare_commits.sh <branch_origem> <branch_destino> <quantidade_meses> <caminho_projeto> <caminho_saida>"
  exit 1
fi

# Verifica se o diretório do projeto existe
if [ ! -d "$PROJECT_PATH" ]; then
    echo "Erro: Diretório do projeto $PROJECT_PATH não existe"
    exit 1
fi

# Verifica se o diretório de saída existe
if [ ! -d "$OUTPUT_PATH" ]; then
    echo "Erro: Diretório de saída $OUTPUT_PATH não existe"
    exit 1
fi

# Define o nome do arquivo de saída
OUTPUT_FILE="$OUTPUT_PATH/commits_comparacao.csv"

# Entra no diretório do projeto
cd "$PROJECT_PATH" || exit 1

# Verifica se é um repositório git
if [ ! -d ".git" ]; then
    echo "Erro: $PROJECT_PATH não é um repositório git"
    exit 1
fi

# Atualiza branches
echo "Atualizando repositório..."
git fetch

# Data limite
SINCE_DATE=$(date -d "-$MESES months" +%Y-%m-%d)

# Header do CSV
echo "Commit;Autor;Data;Mensagem;Presente_na_${BRANCH_DESTINO};Eh_Merge" > "$OUTPUT_FILE"

# Lista commits da branch origem desde a data limite
echo "Analisando commits..."
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
  echo "$HASH;$AUTOR;$DATA;$MSG;$PRESENTE;$EH_MERGE" >> "$OUTPUT_FILE"
done

echo "Análise concluída!"
echo "Arquivo gerado em: $OUTPUT_FILE"