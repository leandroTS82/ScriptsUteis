param(
    [Parameter(Mandatory = $true)]
    [string]$RootPath,

    # Critério de busca (padrão: *.en.txt)
    [string]$Pattern = "*.en.txt",

    # Pasta de saída
    [string]$OutputFolder = "./output",

    # Nome do arquivo final mesclado
    [string]$MergedFileName = "merged_output.txt"
)

# Criar pasta de saída se não existir
if (-not (Test-Path $OutputFolder)) {
    New-Item -ItemType Directory -Path $OutputFolder | Out-Null
}

Write-Host "🔍 Procurando arquivos em: $RootPath"
Write-Host "📌 Critério: $Pattern"
Write-Host "📁 Saída: $OutputFolder"
Write-Host ""

# Buscar arquivos recursivamente
$files = Get-ChildItem -Path $RootPath -Recurse -ErrorAction SilentlyContinue | 
         Where-Object { -not $_.PSIsContainer -and $_.Name -like $Pattern }

if (-not $files -or $files.Count -eq 0) {
    Write-Host "⚠ Nenhum arquivo encontrado."
    exit
}

# Copiar arquivos encontrados
foreach ($file in $files) {
    $dest = Join-Path $OutputFolder $file.Name
    Copy-Item $file.FullName $dest -Force
    Write-Host "✅ Copiado: $($file.FullName)"
}

# Caminho do arquivo mesclado
$mergedFilePath = Join-Path $OutputFolder $MergedFileName

# Apagar o arquivo anterior, se existir
if (Test-Path $mergedFilePath) {
    Remove-Item $mergedFilePath -Force
}

Write-Host ""
Write-Host "📝 Gerando arquivo mesclado: $mergedFilePath"
Write-Host ""

# Criar e montar o arquivo mesclado
foreach ($file in $files) {
    $header = @"
========================================
FILE: $($file.Name)
PATH: $($file.FullName)
========================================

"@

    Add-Content -Path $mergedFilePath -Value $header

    Get-Content $file.FullName | Add-Content -Path $mergedFilePath

    Add-Content -Path $mergedFilePath -Value "`n`n"
}

Write-Host "✔ Concluído!"
Write-Host "📄 Total de arquivos copiados: $($files.Count)"
Write-Host "📘 Arquivo mesclado gerado: $MergedFileName"

# .\17-Find-And-Copy-Files.ps1 -RootPath "C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\Communication site - ReunioesGravadas"