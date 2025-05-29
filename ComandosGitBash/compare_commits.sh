#!/bin/bash

#===================================================================================
# Script: compare_commits.sh
# 
# Descrição:
#   Script para comparar commits entre duas branches do Git, identificando commits
#   que foram cherry-picked através de análise de conteúdo e mensagens. Gera um
#   relatório CSV com informações detalhadas sobre cada commit.
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
#   - Status na branch destino (IGUAL_EXATO/SIMILAR/NAO)
#   - É commit de merge
#
# Status possíveis:
#   IGUAL_EXATO - Commit com mensagem e conteúdo idênticos
#   SIMILAR     - Commit com conteúdo similar (provável cherry-pick)
#   NAO         - Commit não encontrado na branch destino
#===================================================================================

# Variáveis de entrada
BRANCH_ORIGEM=$1
BRANCH_DESTINO=$2
MESES=$3
PROJECT_PATH=$4
OUTPUT_PATH=$5

# Função para comparar commits
# Parâmetros:
#   $1 - Hash do commit de origem
#   $2 - Mensagem do commit de origem
compare_commit() {
    local hash=$1
    local msg=$2
    local patch_origem=$(git show --pretty=format:"" --patch $hash)
    
    # Procura por commits na branch destino com mensagem similar
    git log $BRANCH_DESTINO --since="$SINCE_DATE" --pretty=format:"%H" | while read destino_hash
    do
        local destino_msg=$(git log -1 --pretty=format:"%s" $destino_hash)
        local patch_destino=$(git show --pretty=format:"" --patch $destino_hash)
        
        # Compara primeiro por mensagem exata
        if [ "$msg" = "$destino_msg" ]; then
            # Se mensagem for igual, compara o patch
            if [ "$patch_origem" = "$patch_destino" ]; then
                echo "IGUAL_EXATO"
                return 0
            fi
        fi
        
        # Compara por similaridade de patch (ignora whitespace e contexto)
        if diff -w -B <(echo "$patch_origem") <(echo "$patch_destino") >/dev/null; then
            echo "SIMILAR"
            return 0
        fi
    done
    
    echo "NAO"
    return 1
}

# Validação de argumentos
if [ -z "$BRANCH_ORIGEM" ] || [ -z "$BRANCH_DESTINO" ] || [ -z "$MESES" ] || [ -z "$PROJECT_PATH" ] || [ -z "$OUTPUT_PATH" ]; then
    echo "Uso: ./compare_commits.sh <branch_origem> <branch_destino> <quantidade_meses> <caminho_projeto> <caminho_saida>"
    echo "Exemplo: ./compare_commits.sh develop main 3 /path/to/project /path/to/output"
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

# Verifica se as branches existem
if ! git show-ref --verify --quiet "refs/remotes/origin/$BRANCH_ORIGEM"; then
    echo "Erro: Branch '$BRANCH_ORIGEM' não existe no repositório remoto"
    exit 1
fi

if ! git show-ref --verify --quiet "refs/remotes/origin/$BRANCH_DESTINO"; then
    echo "Erro: Branch '$BRANCH_DESTINO' não existe no repositório remoto"
    exit 1
fi

# Data limite
SINCE_DATE=$(date -d "-$MESES months" +%Y-%m-%d)

# Header do CSV
echo "Commit;Autor;Data;Mensagem;Status_na_${BRANCH_DESTINO};Eh_Merge" > "$OUTPUT_FILE"

# Lista commits da branch origem desde a data limite
echo "Analisando commits..."
git log $BRANCH_ORIGEM --since="$SINCE_DATE" --pretty=format:"%H;%an;%ad;%s" --date=iso | while IFS=";" read HASH AUTOR DATA MSG
do
    echo "Analisando commit: $HASH"
    
    # Verifica status do commit
    STATUS=$(compare_commit "$HASH" "$MSG")
    
    # Verifica se é um commit de merge
    PARENTS=$(git rev-list --parents -n 1 $HASH)
    NUM_PARENTS=$(echo $PARENTS | wc -w)
    if [ "$NUM_PARENTS" -gt 2 ]; then
        EH_MERGE="SIM"
    else
        EH_MERGE="NAO"
    fi
    
    # Escreve no CSV
    echo "$HASH;$AUTOR;$DATA;$MSG;$STATUS;$EH_MERGE" >> "$OUTPUT_FILE"
done

echo "Análise concluída!"
echo "Arquivo gerado em: $OUTPUT_FILE"