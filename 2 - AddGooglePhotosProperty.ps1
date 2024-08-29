# AddGooglePhotosProperty.ps1

# Define o diretório de origem
$sourceDirectory = "C:\Users\leand\Downloads"

# Define a propriedade e o valor que será adicionado
$propertyName = "GooglePhotos"
$propertyValue = "Migrado do Google Fotos"

# Função para adicionar as informações aos arquivos de mídia
function Add-PropertyFile {
    param (
        [string]$filePath,
        [string]$propertyName,
        [string]$propertyValue
    )

    $propertyFilePath = "$filePath.txt"

    if (-not (Test-Path -Path $propertyFilePath)) {
        "${propertyName}: ${propertyValue}" | Out-File -FilePath $propertyFilePath
        Write-Host "Propriedade '${propertyName}' adicionada ao arquivo: $propertyFilePath" -ForegroundColor Green
    } else {
        Write-Host "Propriedade '${propertyName}' já existe para o arquivo: $propertyFilePath" -ForegroundColor Yellow
    }
}

# Obtém todos os arquivos nas pastas e subpastas do diretório de origem
$files = Get-ChildItem -Path $sourceDirectory -Recurse -File

foreach ($file in $files) {
    Add-PropertyFile -filePath $file.FullName -propertyName $propertyName -propertyValue $propertyValue
}

Write-Host "Propriedades adicionadas com sucesso a todos os arquivos." -ForegroundColor Cyan
