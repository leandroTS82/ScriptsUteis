#!/bin/bash
#===================================================================================
# Script: git-push-script.sh
# 
# Descrição:
#   Script para automatizar o processo de push no Git com verificações de segurança,
#   validações e merge automático com a branch produtiva.
#
# Uso:
#   ./git-push-script.sh <caminho_do_projeto>
#
# Exemplo de execução:
#   ./git-push-script.sh /caminho/do/projeto
#
# Funcionalidades:
#   - Verifica se o diretório e o repositório Git são válidos
#   - Realiza pull automático da branch produtiva
#   - Realiza merge automático com a branch produtiva
#   - Push automático se não houver conflitos
#   - Feedback amigável em caso de erros
#
# Versão: 1.1
#===================================================================================

# Define a branch produtiva
productive_branch="main"

# Recebe o caminho do projeto como variável
project_path=$1

# Função para exibir mensagens de erro de forma amigável
error_exit() {
    echo "❌ Ops! Algo deu errado..."
    echo "🔍 Detalhes: $1"
    echo "💡 Sugestão: Verifique o erro acima e tente novamente"
    exit 1
}

# Função para verificar se o Git está instalado
check_git_version() {
    if ! command -v git >/dev/null 2>&1; then
        error_exit "Parece que o Git não está instalado no seu sistema"
    fi
}

# Verifica se foi fornecido o caminho do projeto
if [ -z "$project_path" ]; then
    error_exit "Por favor, informe o caminho do projeto"
fi

# Verifica se o diretório existe
if [ ! -d "$project_path" ]; then
    error_exit "Não encontrei o diretório: $project_path"
fi

# Verifica se Git está instalado
check_git_version

# Entra no diretório do projeto
cd "$project_path" || error_exit "Não consegui acessar o diretório do projeto"

# Verifica se é um repositório git
if [ ! -d ".git" ]; then
    error_exit "Este diretório não parece ser um repositório Git"
fi

echo "🚀 Trabalhando no projeto: $project_path"

# Guarda a branch atual
current_branch=$(git rev-parse --abbrev-ref HEAD)
echo "📂 Branch atual: $current_branch"

# Verifica status do repositório
echo -e "\n📋 Verificando status do repositório..."
if [ -n "$(git status --porcelain)" ]; then
    error_exit "Existem alterações não commitadas. Por favor, faça commit ou stash das alterações primeiro"
fi

echo "🔄 Iniciando processo de atualização..."

# Tenta mudar para a branch produtiva
echo "📍 Mudando para branch $productive_branch..."
if ! git checkout $productive_branch; then
    error_exit "Não foi possível mudar para a branch $productive_branch"
fi

# Atualiza a branch produtiva
echo "⬇️ Atualizando branch $productive_branch..."
if ! git pull origin $productive_branch; then
    error_exit "Erro ao atualizar a branch $productive_branch"
fi

# Volta para a branch original
echo "📍 Voltando para branch $current_branch..."
if ! git checkout $current_branch; then
    error_exit "Não foi possível voltar para a branch $current_branch"
fi

# Atualiza a branch atual
echo "⬇️ Atualizando branch $current_branch..."
if ! git pull origin $current_branch; then
    error_exit "Erro ao atualizar a branch $current_branch"
fi

# Tenta realizar o merge
echo "🔄 Realizando merge com $productive_branch..."
if ! git merge $productive_branch --no-commit; then
    echo "❌ Conflitos detectados durante o merge!"
    echo "🔧 Por favor:"
    echo "1. Resolva os conflitos manualmente"
    echo "2. Faça commit das alterações"
    echo "3. Execute o script novamente"
    git merge --abort
    exit 1
fi

# Verifica se há alterações após o merge
if [ -n "$(git diff --cached)" ]; then
    # Finaliza o merge com commit
    if ! git commit -m "Merge com $productive_branch"; then
        error_exit "Erro ao finalizar o merge"
    fi
fi

# Realiza o push
echo "⬆️ Realizando push das alterações..."
if ! git push origin $current_branch; then
    error_exit "Erro ao realizar push para origin/$current_branch"
fi

echo "✨ Processo concluído com sucesso!"
echo "📋 Resumo:"
echo "- Branch atual: $current_branch"
echo "- Merge realizado com: $productive_branch"
echo "- Push realizado para: origin/$current_branch"