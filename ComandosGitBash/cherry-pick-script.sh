#!/bin/bash
#===================================================================================
# Script: cherry-pick-script.sh
# 
# Descrição:
#   Script para automatizar e tornar mais seguro o processo de cherry-pick no Git.
#   Realiza várias verificações de segurança e oferece confirmações antes de 
#   executar o cherry-pick, além de lidar com commits de merge e conflitos.
#
# Uso:
#   ./cherry-pick-script.sh <caminho_do_projeto> <hash_do_commit>
#
# Exemplo de execução:
#   ./cherry-pick-script.sh /caminho/do/projeto abc123def456
#
# Funcionalidades:
#   - Verifica se o diretório e o repositório Git são válidos
#   - Mostra detalhes do commit antes do cherry-pick
#   - Identifica se é um commit de merge
#   - Verifica branches locais e remotas que contêm o commit
#   - Oferece opções para lidar com conflitos e commits vazios
#   - Valida se o cherry-pick foi bem sucedido
#
# Autor: [Seu Nome]
# Data: [Data de Criação]
# Versão: 1.4
#===================================================================================

# Recebe o caminho do projeto e o hash como variáveis
project_path=$1
hash=$2

# Função para exibir mensagens de erro
error_exit() {
    echo "❌ Erro: $1"
    exit 1
}

# Função para verificar se o Git está instalado e sua versão
check_git_version() {
    if ! command -v git >/dev/null 2>&1; then
        error_exit "Git não está instalado"
    fi
    
    required_git_version="2.0.0"
    git_version=$(git --version | cut -d' ' -f3)
    if ! [[ $(printf '%s\n' "$required_git_version" "$git_version" | sort -V | head -n1) = "$required_git_version" ]]; then
        error_exit "Git $required_git_version ou superior é necessário"
    fi
}

# Função de limpeza
cleanup() {
    if [ -n "$(git status --porcelain)" ]; then
        echo "🧹 Limpando estado do repositório..."
        git cherry-pick --abort 2>/dev/null
        git stash pop 2>/dev/null
    fi
}

# Configurar trap para SIGINT e SIGTERM
trap 'echo "⚠️ Script interrompido"; cleanup; exit 1' INT TERM

# Verifica se foram fornecidos os argumentos necessários
if [ -z "$project_path" ] || [ -z "$hash" ]; then
    error_exit "Uso: $0 <caminho_do_projeto> <hash>"
fi

# Verifica se o diretório existe
if [ ! -d "$project_path" ]; then
    error_exit "Diretório $project_path não existe"
fi

# Verifica versão do Git
check_git_version

# Entra no diretório do projeto
cd "$project_path" || error_exit "Não foi possível acessar o diretório"

# Verifica se é um repositório git
if [ ! -d ".git" ]; then
    error_exit "$project_path não é um repositório git"
fi

# Verifica se o hash é válido
if ! git cat-file -e "$hash^{commit}" 2>/dev/null; then
    error_exit "Hash $hash não é válido"
fi

# Verifica se há mudanças não commitadas
if ! git diff-index --quiet HEAD --; then
    echo "⚠️ Existem mudanças não commitadas no repositório"
    read -p "Deseja fazer stash das mudanças antes de continuar? (s/n): " resposta
    if [[ $resposta == "s" ]]; then
        git stash save "Backup antes do cherry-pick de $hash"
    else
        error_exit "Operação cancelada - Commit ou stash das mudanças primeiro"
    fi
fi

echo "🚀 Trabalhando no projeto: $project_path"

# Função para verificar branches que contêm o commit
check_branches() {
    local hash=$1
    
    echo -e "\n=== Branches Locais que contêm o commit ==="
    git branch --contains $hash
    
    echo -e "\n=== Branches Remotas que contêm o commit ==="
    git branch -r --contains $hash
    
    # Verifica se o commit está em alguma branch importante
    if git branch --contains $hash | grep -q "main\|master\|develop"; then
        echo -e "\n⚠️  ATENÇÃO: Este commit está presente em branches principais!"
    fi
    
    if git branch -r --contains $hash | grep -q "origin/main\|origin/master\|origin/develop"; then
        echo -e "\n⚠️  ATENÇÃO: Este commit está presente em branches principais remotas!"
    fi
}

# Função para lidar com cherry-pick em andamento
handle_ongoing_cherry_pick() {
    echo "🔄 Detectado cherry-pick em andamento..."
    
    # Verifica status do cherry-pick
    status_output=$(git status)
    
    if echo "$status_output" | grep -q "all conflicts fixed"; then
        echo "✅ Todos os conflitos foram resolvidos."
        echo "Opções:"
        echo "1. Continuar com cherry-pick (git cherry-pick --continue)"
        echo "2. Pular este commit (git cherry-pick --skip)"
        echo "3. Abortar cherry-pick"
        read -p "Escolha uma opção (1/2/3): " opcao
        
        case $opcao in
            1)
                if git cherry-pick --continue; then
                    echo "✅ Cherry-pick continuado com sucesso!"
                    return 0
                else
                    error_exit "Erro ao continuar o cherry-pick"
                fi
                ;;
            2)
                git cherry-pick --skip
                echo "⏭️ Cherry-pick pulado"
                return 0
                ;;
            3)
                git cherry-pick --abort
                echo "⛔ Cherry-pick abortado"
                return 1
                ;;
            *)
                error_exit "Opção inválida"
                ;;
        esac
    elif echo "$status_output" | grep -q "cherry-pick is now empty"; then
        echo "ℹ️ O cherry-pick resultou em um commit vazio"
        echo "Opções:"
        echo "1. Criar commit vazio (git commit --allow-empty)"
        echo "2. Pular este commit (git cherry-pick --skip)"
        echo "3. Abortar cherry-pick"
        read -p "Escolha uma opção (1/2/3): " opcao
        
        case $opcao in
            1)
                git commit --allow-empty -C "$hash"
                echo "✅ Commit vazio criado"
                return 0
                ;;
            2)
                git cherry-pick --skip
                echo "⏭️ Cherry-pick pulado"
                return 0
                ;;
            3)
                git cherry-pick --abort
                echo "⛔ Cherry-pick abortado"
                return 1
                ;;
            *)
                error_exit "Opção inválida"
                ;;
        esac
    else
        echo "⚠️ Existem conflitos não resolvidos"
        return 1
    fi
}

# Função para lidar com o cherry-pick
do_cherry_pick() {
    local hash=$1
    local is_merge=$2
    
    # Verifica se há um cherry-pick em andamento
    if [ -f ".git/CHERRY_PICK_HEAD" ]; then
        handle_ongoing_cherry_pick
        return $?
    fi
    
    # Faz backup do estado atual
    echo "📦 Criando backup do estado atual..."
    git stash save "Backup antes do cherry-pick de $hash" >/dev/null 2>&1
    
    echo "🔄 Iniciando cherry-pick..."
    if [ $is_merge -gt 1 ]; then
        git cherry-pick -m 1 $hash
    else
        git cherry-pick $hash
    fi
    
    # Captura a saída do status
    status_output=$(git status)
    
    # Verifica diferentes cenários
    if echo "$status_output" | grep -q "nothing to commit, working tree clean"; then
        if echo "$status_output" | grep -q "previous cherry-pick is now empty"; then
            echo "ℹ️ O cherry-pick resultou em um commit vazio"
            echo "Opções:"
            echo "1. Criar commit vazio (git commit --allow-empty)"
            echo "2. Pular este commit (git cherry-pick --skip)"
            echo "3. Abortar cherry-pick"
            read -p "Escolha uma opção (1/2/3): " opcao
            
            case $opcao in
                1)
                    git commit --allow-empty -C "$hash"
                    echo "✅ Commit vazio criado"
                    return 0
                    ;;
                2)
                    git cherry-pick --skip
                    echo "⏭️ Cherry-pick pulado"
                    return 0
                    ;;
                3)
                    git cherry-pick --abort
                    git stash pop >/dev/null 2>&1
                    echo "⛔ Cherry-pick abortado"
                    return 1
                    ;;
                *)
                    error_exit "Opção inválida"
                    ;;
            esac
        else
            echo "✅ Cherry-pick realizado com sucesso!"
            return 0
        fi
    elif echo "$status_output" | grep -q "fix conflicts"; then
        echo "⚠️ CONFLITO detectado durante o cherry-pick!"
        echo "Opções:"
        echo "1. Resolver conflitos manualmente"
        echo "2. Abortar cherry-pick e restaurar backup"
        read -p "Escolha uma opção (1/2): " opcao
        
        case $opcao in
            1)
                echo "🔧 Por favor, resolva os conflitos manualmente."
                echo "Após resolver, execute:"
                echo "git add ."
                echo "git cherry-pick --continue"
                echo "Script interrompido para resolução manual."
                exit 1
                ;;
            2)
                git cherry-pick --abort
                git stash pop >/dev/null 2>&1
                echo "⛔ Cherry-pick abortado e backup restaurado"
                exit 1
                ;;
            *)
                git cherry-pick --abort
                git stash pop >/dev/null 2>&1
                error_exit "Opção inválida"
                ;;
        esac
    fi
}

# Atualiza a lista de branches remotas
echo "🔄 Atualizando informações das branches remotas..."
git fetch --all

# Mostra o commit
echo -e "\n📄 Exibindo detalhes do commit..."
git show $hash

# Pede confirmação para continuar
read -p "Deseja continuar? (s/n): " resposta
if [[ $resposta != "s" ]]; then
    echo "⛔ Operação cancelada"
    exit 0
fi

# Verifica as branches que contêm o commit
echo -e "\n🔍 Verificando branches que contêm o commit..."
check_branches $hash

# Pede confirmação novamente
read -p "Deseja continuar com o cherry-pick? (s/n): " resposta
if [[ $resposta != "s" ]]; then
    echo "⛔ Operação cancelada"
    exit 0
fi

# Verifica se é um commit de merge
is_merge=$(git cat-file -p $hash | grep -c "^parent ")
if [ $is_merge -gt 1 ]; then
    echo "⚠️ ATENÇÃO: Este é um commit de merge!"
    echo "Detalhes do merge:"
    git show --format="%h %s" $hash
    
    read -p "Deseja realizar o cherry-pick mesmo assim? (s/n): " resposta
    if [[ $resposta == "s" ]]; then
        echo "🔄 Realizando cherry-pick do merge commit..."
        do_cherry_pick $hash $is_merge
    else
        echo "⛔ Operação cancelada"
        exit 0
    fi
else
    echo "🔄 Realizando cherry-pick..."
    do_cherry_pick $hash $is_merge
fi

echo "✨ Processo concluído!"