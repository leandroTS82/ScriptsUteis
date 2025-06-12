# Script PowerShell para mostrar estrutura simplificada do projeto e salvar em arquivo

# Defina o caminho raiz do projeto
$projectPath = "C:\dev\Android\MAUI\CantinaV1"

# Arquivo de saída
$outputFile = Join-Path $projectPath "estrutura_simplificada.txt"

# Pastas que quer listar na estrutura (pode ajustar)
$foldersToList = @("Data", "Models", "Services", "Views")

# Descrição para cada pasta (pode ajustar)
$folderDescriptions = @{
    "Models" = "(Modelos de dados)"
    "Services" = @"
├── Externals        (Serviços externos: Firebase, WhatsApp, CSV, XLSX)
└── Internals        (Serviços internos: Pedidos, Produtos, Configurações)
"@
    "ViewModels" = "(ViewModels - atualmente vazio)"
    "Views" = "(Páginas de interface do usuário)"
    "Resources" = "(Estilos, Cores)"
}

# Limpa o arquivo de saída se existir
if (Test-Path $outputFile) {
    Remove-Item $outputFile
}

# Função para listar arquivos e pastas dentro de uma pasta, com indentação
function List-FolderContent {
    param(
        [string]$path,
        [int]$indentLevel
    )

    $indent = "│   " * $indentLevel

    # Listar subdiretórios
    $dirs = Get-ChildItem -Path $path -Directory | Sort-Object Name
    foreach ($dir in $dirs) {
        Add-Content $outputFile "$indent├── $($dir.Name)"
        # Recursivamente listar o conteúdo das subpastas
        List-FolderContent -path $dir.FullName -indentLevel ($indentLevel + 1)
    }

    # Listar arquivos
    $files = Get-ChildItem -Path $path -File | Sort-Object Name
    foreach ($file in $files) {
        Add-Content $outputFile "$indent└── $($file.Name)"
    }
}

# Escreve cabeçalho
Add-Content $outputFile "MauiCantinaV1"
Add-Content $outputFile "│"

foreach ($folder in $foldersToList) {
    $fullPath = Join-Path $projectPath $folder

    if (-Not (Test-Path $fullPath)) {
        Add-Content $outputFile "├── $folder (folder not found)"
        Add-Content $outputFile "│"
        continue
    }

    if ($folder -eq "Services") {
        # Pasta Services especial com subpastas fixas e descrição
        Add-Content $outputFile "├── $folder"
        $indentServices = "│   "
        Add-Content $outputFile "$indentServices├── Externals        (Serviços externos: Firebase, WhatsApp, CSV, XLSX, txt etc)"
        $externalsPath = Join-Path $fullPath "Externals"
        if (Test-Path $externalsPath) {
            List-FolderContent -path $externalsPath -indentLevel 2
        }
        Add-Content $outputFile "$indentServices└── Internals        (Serviços internos: Pedidos, Produtos, Configurações etc)"
        $internalsPath = Join-Path $fullPath "Internals"
        if (Test-Path $internalsPath) {
            List-FolderContent -path $internalsPath -indentLevel 2
        }
        Add-Content $outputFile "│"
    }
    else {
        $desc = $folderDescriptions[$folder]
        if ($desc) {
            Add-Content $outputFile "├── $folder           $desc"
        }
        else {
            Add-Content $outputFile "├── $folder"
        }

        # Listar conteúdo da pasta com indentação 1
        List-FolderContent -path $fullPath -indentLevel 1
        Add-Content $outputFile "│"
    }
}

# Listar arquivos raiz .xaml, .cs, .json, .config, .xml como "Root Files"
$rootFiles = Get-ChildItem -Path $projectPath -File | Where-Object { $_.Extension -match "(\.xaml|\.cs|\.json|\.config|\.xml)" } | Sort-Object Name
if ($rootFiles.Count -gt 0) {
    $fileNames = $rootFiles | ForEach-Object { $_.Name }
    $fileList = $fileNames -join ", "
    Add-Content $outputFile "└── Root Files          ($fileList)"
} else {
    Add-Content $outputFile "└── Root Files"
}

Write-Output "Estrutura simplificada gerada no arquivo $outputFile"