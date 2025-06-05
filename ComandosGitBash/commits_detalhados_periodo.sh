#!/bin/bash

#===================================================================================
# Script: commits_detalhados_periodo.sh
# 
# Descrição:
#   Script para listar commits detalhados de uma branch específica em um determinado
#   período de meses, gerando um relatório em formato CSV. O script inclui informações
#   como hash do commit, autor, email, data, mensagem e se é um commit de merge.
#
# Uso:
#   ./commits_detalhados_periodo.sh <branch> <meses> <caminho_projeto> <caminho_saida>
#
# Parâmetros:
#   branch          - Nome da branch para análise
#   meses           - Período em meses para análise retroativa
#   caminho_projeto - Caminho do repositório Git
#   caminho_saida   - Caminho onde o arquivo CSV será gerado
#
# Exemplo de execução:
#   ./commits_detalhados_periodo.sh develop 3 /path/to/project /path/to/output
#
# Saída:
#   Gera um arquivo CSV com as colunas:
#   - Commit (hash)
#   - Autor
#   - Email
#   - Data
#   - Mensagem
#   - É commit de merge
#===================================================================================

# Variáveis de entrada
BRANCH=$1
MESES=$2
PROJECT_PATH=$3
OUTPUT_PATH=$4

# Validação de parâmetros
if [ -z "$BRANCH" ] || [ -z "$MESES" ] || [ -z "$PROJECT_PATH" ] || [ -z "$OUTPUT_PATH" ]; then
    echo "Uso: ./commits_detalhados_periodo.sh <branch> <meses> <caminho_projeto> <caminho_saida>"
    echo "Exemplo: ./commits_detalhados_periodo.sh develop 3 /path/to/project /path/to/output"
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

# Define nome do arquivo de saída
OUTPUT_FILE="$OUTPUT_PATH/$(echo $BRANCH | tr '/' '-')_ultimos_${MESES}_meses.csv"

# Entra no diretório do projeto
cd "$PROJECT_PATH" || exit 1

# Verifica se é um repositório git
if [ ! -d ".git" ]; then
    echo "Erro: $PROJECT_PATH não é um repositório git"
    exit 1
fi

# Atualiza referências remotas
echo "Atualizando repositório..."
git fetch origin

# Verifica se a branch existe
if ! git show-ref --verify --quiet "refs/remotes/origin/$BRANCH"; then
    echo "Erro: Branch '$BRANCH' não existe no repositório remoto"
    exit 1
fi

# Faz checkout da branch
echo "Mudando para a branch $BRANCH..."
if ! git checkout $BRANCH 2>/dev/null; then
    echo "Aviso: Não foi possível mudar para a branch $BRANCH"
    echo "Continuando com a análise mesmo assim..."
fi

# Define data limite para filtro
SINCE_DATE=$(date -d "-$MESES months" +%Y-%m-%d)

# Cabeçalho do CSV
echo "Commit;Autor;Email;Data;Mensagem;Eh_Merge" > "$OUTPUT_FILE"

# Lista commits desde a data limite
echo "Analisando commits..."
git log $BRANCH --since="$SINCE_DATE" --pretty=format:"%H;%an;%ae;%ad;%s" --date=iso | while IFS=";" read HASH AUTOR EMAIL DATA MSG
do
    # Verifica se é um commit de merge
    PARENTS=$(git rev-list --parents -n 1 $HASH)
    NUM_PARENTS=$(echo $PARENTS | wc -w)
    if [ "$NUM_PARENTS" -gt 2 ]; then
        EH_MERGE="SIM"
    else
        EH_MERGE="NAO"
    fi
    
    # Escreve no CSV
    echo "$HASH;$AUTOR;$EMAIL;$DATA;$MSG;$EH_MERGE" >> "$OUTPUT_FILE"
done

echo "Análise concluída!"
echo "Arquivo gerado em: $OUTPUT_FILE"