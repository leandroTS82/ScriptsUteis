# ================================================================
# Script: Fix-Playlist.ps1
# Autor: Leandro
# Finalidade:
#   - Ler todos os JSONs da pasta configurada
#   - Encontrar "playlists": []
#   - Usar o primeiro valor para gerar a estrutura correta:
#
#     "playlist": {
#         "Id": "",
#         "create_if_not_exists": true,
#         "name": "Valor recuperado",
#         "description": ""
#     }
#
#   - Remover o campo "playlists"
#   - Reescrever o JSON corrigido
# ================================================================


# 🎯 PASTA FIXA DOS JSONS
$FolderPath = "C:\\Users\\leand\\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\\LTS SP Site - VideosGeradosPorScript\\Videos"

Write-Host " Lendo JSONs da pasta fixa: $FolderPath" -ForegroundColor Cyan

# Verifica se a pasta existe
if (-not (Test-Path $FolderPath)) {
    Write-Host "❌ ERRO: A pasta configurada não existe." -ForegroundColor Red
    exit
}

# Lista todos os arquivos JSON
$jsonFiles = Get-ChildItem -Path $FolderPath -Filter "*.json"

if ($jsonFiles.Count -eq 0) {
    Write-Host "⚠ Nenhum arquivo JSON encontrado." -ForegroundColor Yellow
    exit
}

foreach ($file in $jsonFiles) {

    Write-Host "`n➡ Processando arquivo: $($file.Name)" -ForegroundColor Green

    try {
        # Ler JSON
        $jsonContent = Get-Content -Path $file.FullName -Raw -Encoding UTF8
        $jsonObj = $jsonContent | ConvertFrom-Json
    }
    catch {
        Write-Host "❌ Erro ao ler JSON: $($file.Name)" -ForegroundColor Red
        continue
    }

    # Verifica se existe playlists
    if ($jsonObj.playlists -and $jsonObj.playlists.Count -gt 0) {

        $firstPlaylist = $jsonObj.playlists[0]

        Write-Host "🎯 Playlist encontrada: $firstPlaylist"

        # Estrutura final correta
        $finalPlaylist = @{
            Id = ""
            create_if_not_exists = $true
            name = $firstPlaylist
            description = ""
        }

        # Adicionar/atualizar a playlist correta
        $jsonObj | Add-Member -MemberType NoteProperty -Name "playlist" -Value $finalPlaylist -Force

        # Remover campo errado
        $jsonObj.PSObject.Properties.Remove("playlists")

        # Converter de volta para JSON formatado
        $newJson = $jsonObj | ConvertTo-Json -Depth 10

        # Reescrever arquivo
        Set-Content -Path $file.FullName -Value $newJson -Encoding UTF8

        Write-Host "✔ JSON atualizado com sucesso!" -ForegroundColor Cyan
    }
    else {
        Write-Host "⚠ Campo 'playlists' não encontrado ou vazio. Arquivo ignorado."
    }
}

Write-Host "`n  Processo concluído com sucesso!" -ForegroundColor Magenta
