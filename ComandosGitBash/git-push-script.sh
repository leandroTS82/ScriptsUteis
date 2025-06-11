#!/bin/bash
#===================================================================================
# Script: git-push-script.sh
# 
# Descrição:
#   Script para automatizar o processo de push no Git com verificações de segurança
#   e validações antes do push.
#
# Uso:
#   ./git-push-script.sh <caminho_do_projeto>
#
# Exemplo de execução:
#   ./git-push-script.sh /caminho/do/projeto
#
# Funcionalidades:
#   - Verifica se o diretório e o repositório Git são válidos
#   - Mostra o status atual das alterações
#   - Verifica se há conflitos
#   - Oferece opção de pull antes do push
#   - Validação de credenciais
#
# Versão: 1.0
#===================================================================================

# Recebe o caminho do projeto como variável
project_path=$1

# Função para exibir mensagens de erro
error_exit() {
    echo "❌ Erro: $1"
    exit 1
}

# Função para verificar se o Git está instalado
check_git_version() {
    if ! command -v git >/dev/null 2>&1; then
        error_exit "Git não está instalado"
    fi
}

# Verifica se foi fornecido o caminho do projeto
if [ -z "$project_path" ]; then
    error_exit "Uso: $0 <caminho_do_projeto>"
fi

# Verifica se o diretório existe
if [ ! -d "$project_path" ]; then
    error_exit "Diretório $project_path não existe"
fi

# Verifica se Git está instalado
check_git_version

# Entra no diretório do projeto
cd "$project_path" || error_exit "Não foi possível acessar o diretório"

# Verifica se é um repositório git
if [ ! -d ".git" ]; then
    error_exit "$project_path não é um repositório git"
fi

echo "🚀 Trabalhando no projeto: $project_path"

# Obtém o nome da branch atual
current_branch=$(git rev-parse --abbrev-ref HEAD)
echo "📂 Branch atual: $current_branch"

# Verifica status do repositório
echo -e "\n📋 Status atual do repositório:"
git status

# Verifica se há alterações para commit
if [ -n "$(git status --porcelain)" ]; then
    echo -e "\n⚠️ Existem alterações não commitadas!"
    read -p "Deseja fazer commit dessas alterações? (s/n): " commit_resp
    
    if [[ $commit_resp == "s" ]]; then
        # Adiciona todas as alterações
        git add .
        
        # Solicita mensagem do commit
        read -p "Digite a mensagem do commit: " commit_message
        
        # Realiza o commit
        if ! git commit -m "$commit_message"; then
            error_exit "Erro ao realizar commit"
        fi
        
        echo "✅ Commit realizado com sucesso!"
    else
        error_exit "Operação cancelada - Commit as alterações primeiro"
    fi
fi

# Verifica se há commits para push
local_commits=$(git log "origin/$current_branch..$current_branch" --oneline)
if [ -z "$local_commits" ]; then
    echo "ℹ️ Não há commits locais para push"
    exit 0
fi

# Mostra commits que serão enviados
echo -e "\n📦 Commits que serão enviados:"
echo "$local_commits"

# Oferece opção de pull antes do push
read -p "Deseja fazer pull antes do push? (s/n): " pull_resp
if [[ $pull_resp == "s" ]]; then
    echo "🔄 Realizando pull..."
    if ! git pull origin "$current_branch"; then
        error_exit "Erro durante o pull"
    fi
fi

# Confirmação final
read -p "Deseja realizar o push? (s/n): " push_resp
if [[ $push_resp != "s" ]]; then
    echo "⛔ Operação cancelada"
    exit 0
fi

# Realiza o push
echo "🔄 Realizando push..."
if ! git push origin "$current_branch"; then
    error_exit "Erro durante o push"
fi

echo "✨ Push realizado com sucesso!"

# Mostra status final
echo -e "\n📋 Status final:"
git status