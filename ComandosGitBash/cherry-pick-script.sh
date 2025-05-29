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
#   - Verifica branches que contém o commit
#   - Oferece opções para lidar com conflitos
#   - Valida se o cherry-pick foi bem sucedido
#
# Autor: [Seu Nome]
# Data: [Data de Criação]
# Versão: 1.0
#===================================================================================

# Recebe o caminho do projeto e o hash como variáveis
project_path=$1
hash=$2

# Verifica se foram fornecidos os argumentos necessários
if [ -z "$project_path" ] || [ -z "$hash" ]; then
    echo "Uso: $0 <caminho_do_projeto> <hash>"
    exit 1
fi

# Verifica se o diretório existe
if [ ! -d "$project_path" ]; then
    echo "Erro: Diretório $project_path não existe"
    exit 1
fi

# Entra no diretório do projeto
cd "$project_path" || exit 1

# Verifica se é um repositório git
if [ ! -d ".git" ]; then
    echo "Erro: $project_path não é um repositório git"
    exit 1
fi

echo "Trabalhando no projeto: $project_path"

# Mostra o commit
echo "Exibindo detalhes do commit..."
git show $hash

# Pede confirmação para continuar
read -p "Deseja continuar? (s/n): " resposta
if [[ $resposta != "s" ]]; then
    echo "Operação cancelada"
    exit 0
fi

# Mostra as branches que contêm o commit
echo "Verificando branches que contêm o commit..."
git branch --contains $hash

# Pede confirmação novamente
read -p "Deseja continuar? (s/n): " resposta
if [[ $resposta != "s" ]]; then
    echo "Operação cancelada"
    exit 0
fi

# Função para lidar com o cherry-pick
do_cherry_pick() {
    local hash=$1
    local is_merge=$2
    
    if [ $is_merge -gt 1 ]; then
        git cherry-pick -m 1 $hash
    else
        git cherry-pick $hash
    fi
    
    # Verifica o status do cherry-pick
    if [ $? -eq 0 ]; then
        echo "Cherry-pick realizado com sucesso!"
        echo "Verificando se o commit está presente na branch atual..."
        echo "Branches que contém o commit $hash:"
        git branch --contains $hash
        
        # Pega o nome da branch atual
        current_branch=$(git rev-parse --abbrev-ref HEAD)
        
        # Verifica se o hash está na branch atual
        if git branch --contains $hash | grep -q "$current_branch"; then
            echo "✅ Commit foi aplicado com sucesso na branch atual ($current_branch)"
            return 0
        else
            echo "⚠️ AVISO: O commit não aparece na branch atual ($current_branch)"
            echo "Isso pode indicar um problema na operação de cherry-pick"
            read -p "Deseja continuar mesmo assim? (s/n): " resposta
            if [[ $resposta != "s" ]]; then
                echo "Operação cancelada"
                exit 1
            fi
        fi
    else
        echo "CONFLITO detectado durante o cherry-pick!"
        echo "Opções:"
        echo "1. Resolver conflitos manualmente"
        echo "2. Abortar cherry-pick"
        read -p "Escolha uma opção (1/2): " opcao
        
        case $opcao in
            1)
                echo "Por favor, resolva os conflitos manualmente."
                echo "Após resolver, execute:"
                echo "git add ."
                echo "git cherry-pick --continue"
                echo "Script interrompido para resolução manual."
                exit 1
                ;;
            2)
                git cherry-pick --abort
                echo "Cherry-pick abortado"
                exit 1
                ;;
            *)
                echo "Opção inválida"
                git cherry-pick --abort
                exit 1
                ;;
        esac
    fi
}

# Verifica se é um commit de merge
is_merge=$(git cat-file -p $hash | grep -c "^parent ")

if [ $is_merge -gt 1 ]; then
    echo "ATENÇÃO: Este é um commit de merge!"
    echo "Detalhes do merge:"
    git show --format="%h %s" $hash
    
    read -p "Deseja realizar o cherry-pick mesmo assim? (s/n): " resposta
    if [[ $resposta == "s" ]]; then
        echo "Realizando cherry-pick do merge commit..."
        do_cherry_pick $hash $is_merge
    else
        echo "Operação cancelada"
        exit 0
    fi
else
    echo "Realizando cherry-pick..."
    do_cherry_pick $hash $is_merge
fi