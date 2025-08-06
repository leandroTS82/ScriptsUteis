$rootDirectory = "C://Dev/AllSetra/allsetra-admin-portal-backend"
$outputFile = "./allsetra-admin-portal-backend-ScanResult.txt"

# Itens a ignorar
$exceptions = @(
    "node_modules", 
    "bin", 
    ".idea", 
    ".github", 
    "Properties", 
    "obj", 
    ".git", 
    ".vs", 
    "dist", 
    "AllsetraPlatform.BE.Api.csproj", 
    "AllsetraPlatform.BE.Api.csproj.user", 
    "AllsetraPlatform.BE.Api.http", 
    "appsettings.Development.json", 
    "AllsetraPlatform.BE.Data.csproj", 
    "AllsetraPlatform.BE.Infrastructure.csproj", 
    "AllsetraPlatform.BE.Services.csproj", 
    "AllsetraPlatform.BE.Domain.csproj"
)

function ScanProject {
    param(
        [string]$rootDirectory,
        [string]$outputFile,
        [array]$exceptions
    )

    if (-Not (Test-Path $outputFile)) {
        New-Item -Path $outputFile -ItemType File
    }

    Get-ChildItem -Path $rootDirectory -Recurse -Filter "*.cs" | ForEach-Object {
        $filePath = $_.FullName
        $relativePath = $filePath.Substring($rootDirectory.Length)

        # Verifica se o caminho do arquivo ou nome do diretório está na lista de exceções
        $exclude = $false
        foreach ($exception in $exceptions) {
            if ($filePath -like "*$exception*") {
                $exclude = $true
                break
            }
        }

        # Se o arquivo estiver na lista de exceções, ignora
        if ($exclude) {
            return
        }

        $fileContent = Get-Content -Path $filePath

        Add-Content -Path $outputFile -Value "Arquivo: $relativePath"
        Add-Content -Path $outputFile -Value "-----------------------------"
        Add-Content -Path $outputFile -Value $fileContent
        Add-Content -Path $outputFile -Value "`r`n"
    }

    Write-Host "Scan completo! O conteúdo foi salvo em $outputFile"
}

ScanProject -rootDirectory $rootDirectory -outputFile $outputFile -exceptions $exceptions
