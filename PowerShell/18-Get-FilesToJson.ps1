# .\18-Get-FilesToJson.ps1 -DirectoryPath "C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Audios"
param (
    [Parameter(Mandatory = $true)]
    [string]$DirectoryPath
)

# -----------------------------------------
# Validar diretório de entrada
# -----------------------------------------
if (!(Test-Path $DirectoryPath)) {
    Write-Error "O diretório informado não existe: $DirectoryPath"
    exit 1
}

# -----------------------------------------
# Criar pasta ./output se não existir
# -----------------------------------------
$outputDir = Join-Path -Path (Get-Location) -ChildPath "output"

if (!(Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir | Out-Null
}

$outputFile = Join-Path $outputDir "files.json"

# -----------------------------------------
# Coletar arquivos
# -----------------------------------------
$files = Get-ChildItem -Path $DirectoryPath -Recurse -File | ForEach-Object {
    [PSCustomObject]@{
        file = $_.Name
        path = $_.FullName
    }
}

# -----------------------------------------
# Converter para JSON no formato desejado
# -----------------------------------------
$jsonObject = @{
    files = $files
}

$json = $jsonObject | ConvertTo-Json -Depth 10

# -----------------------------------------
# Gravar arquivo
# -----------------------------------------
Set-Content -Path $outputFile -Value $json -Encoding UTF8

Write-Host "✔ JSON gerado em: $outputFile"
