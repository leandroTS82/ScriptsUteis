# Defina o caminho raiz do projeto
$projectPath = "C:\dev\SPFXButterfly"
# Pastas que quer listar na estrutura exemplo: @("Data", "Models", "Services", "Views")
$foldersToList = @("src")

# Caminho do arquivo de saída
$outputFile =  "./estrutura_simplificada.txt"

# Descrições por pasta (pode adicionar mais conforme necessário)
$folderDescriptions = @{
    "webparts" = "Local onde os componentes de webparts são criadas"
    "Models"     = "(Modelos de dados)"
    "Services"   = @"
├── Externals        (Serviços externos: Firebase, WhatsApp, CSV, XLSX)
└── Internals        (Serviços internos: Pedidos, Produtos, Configurações)
"@
    "ViewModels" = "(ViewModels - atualmente vazio)"
    "Views"      = "(Páginas de interface do usuário)"
    "Resources"  = "(Estilos, Cores)"
}

# Apaga o arquivo anterior se existir
if (Test-Path $outputFile) {
    Remove-Item $outputFile
}
# Cabeçalho do arquivo
Add-Content $outputFile "CantinaV1"
Add-Content $outputFile "│"

# Função para listar subpastas e arquivos com indentação
function List-FolderContent {
    param(
        [string]$path,
        [int]$indentLevel
    )

    $indent = "│   " * $indentLevel

    # Listar pastas
    $dirs = Get-ChildItem -Path $path -Directory | Sort-Object Name
    foreach ($dir in $dirs) {
        Add-Content $outputFile "$indent├── $($dir.Name)"
        List-FolderContent -path $dir.FullName -indentLevel ($indentLevel + 1)
    }

    # Listar arquivos
    $files = Get-ChildItem -Path $path -File | Sort-Object Name
    $fileCount = $files.Count
    for ($i = 0; $i -lt $fileCount; $i++) {
        $prefix = if ($i -eq $fileCount - 1) { "└──" } else { "├──" }
        Add-Content $outputFile "$indent$prefix $($files[$i].Name)"
    }
}



# Processar pastas principais
foreach ($folder in $foldersToList) {
    $fullPath = Join-Path $projectPath $folder

    if (-Not (Test-Path $fullPath)) {
        Add-Content $outputFile "├── $folder (folder not found)"
        Add-Content $outputFile "│"
        continue
    }

    if ($folder -eq "Services") {
        Add-Content $outputFile "├── $folder"
        $indentServices = "│   "

        # Externals
        Add-Content $outputFile "$indentServices├── Externals        (Serviços externos: Firebase, WhatsApp, CSV, XLSX, txt etc)"
        $externalsPath = Join-Path $fullPath "Externals"
        if (Test-Path $externalsPath) {
            List-FolderContent -path $externalsPath -indentLevel 2
        }

        # Internals
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

        List-FolderContent -path $fullPath -indentLevel 1
        Add-Content $outputFile "│"
    }
}

# Listar arquivos raiz (extensões ajustáveis aqui)
$rootFiles = Get-ChildItem -Path $projectPath -File | Where-Object {
    $_.Extension -match "(\.xaml|\.cs|\.json|\.config|\.xml)"
} | Sort-Object Name

if ($rootFiles.Count -gt 0) {
    $fileNames = $rootFiles | ForEach-Object { $_.Name }
    $fileList = $fileNames -join ", "
    Add-Content $outputFile "└── Root Files          ($fileList)"
}
else {
    Add-Content $outputFile "└── Root Files"
}

Write-Output "Estrutura simplificada gerada no arquivo $outputFile"