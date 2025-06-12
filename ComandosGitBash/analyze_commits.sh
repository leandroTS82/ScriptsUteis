#!/bin/bash
# ./analyze_commits.sh /caminho/do/projeto 3 /caminho/da/saida

# Função para exibir mensagem de uso do script
show_usage() {
    echo "Uso: $0 <caminho_projeto> <periodo_meses> <caminho_saida>"
    echo "Exemplo: $0 /path/to/project 3 /path/to/output"
    exit 1
}

# Verifica se todos os parâmetros foram fornecidos
if [ "$#" -ne 3 ]; then
    show_usage
fi

# Armazena os parâmetros em variáveis
PROJECT_PATH="$1"
MONTHS="$2"
OUTPUT_PATH="$3"

# Verifica se o diretório do projeto existe
if [ ! -d "$PROJECT_PATH" ]; then
    echo "Erro: Diretório do projeto não encontrado: $PROJECT_PATH"
    exit 1
fi

# Verifica se o diretório de saída existe
if [ ! -d "$OUTPUT_PATH" ]; then
    echo "Erro: Diretório de saída não encontrado: $OUTPUT_PATH"
    exit 1
fi

# Entra no diretório do projeto
cd "$PROJECT_PATH" || exit 1

# Obtém o nome da branch atual
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Define nome do arquivo de saída
OUTPUT_FILE="$OUTPUT_PATH/NaoDevemEstarEmDevIteris_branc_$(echo $CURRENT_BRANCH | tr '/' '-')_${MONTHS}m.csv"


# Cria cabeçalho do CSV
echo "hash,autor,data,mensagem,branches" > "$OUTPUT_FILE"

# Faz pull da branch atual
echo "Atualizando branch $CURRENT_BRANCH..."
git pull origin "$CURRENT_BRANCH"

# Obtém a data de início para filtrar os commits (X meses atrás)
START_DATE=$(date -d "$MONTHS months ago" +%Y-%m-%d)

# Lista todos os commits no período especificado
echo "Obtendo commits dos últimos $MONTHS meses..."
git log --since="$START_DATE" --format="%H|%an|%ad|%s" --date=short | while IFS='|' read -r hash author date message
do
    # Verifica em quais branches o commit está presente
    branches=$(git branch --contains "$hash" | tr -d ' *')
    
    # Flags para verificação
    in_develop=false
    in_develop_iteris=false
    in_newdevelop_iteris=false
    
    # Verifica cada branch
    while IFS= read -r branch; do
        case "$branch" in
            "develop")
                in_develop=true
                ;;
            "develop-iteris")
                in_develop_iteris=true
                ;;
            "newDevelop-iteris")
                in_newdevelop_iteris=true
                ;;
        esac
    done <<< "$branches"
    
    # Aplica a regra de negócio
    if [ "$in_develop" = false ] && { [ "$in_develop_iteris" = true ] || [ "$in_newdevelop_iteris" = true ]; }; then
        # Escapa possíveis vírgulas na mensagem do commit
        message=$(echo "$message" | sed 's/,/;/g')
        # Registra no CSV
        echo "$hash,$author,$date,\"$message\",$branches" >> "$OUTPUT_FILE"
    fi
done

echo "Processo concluído! Arquivo gerado em: $OUTPUT_FILE"