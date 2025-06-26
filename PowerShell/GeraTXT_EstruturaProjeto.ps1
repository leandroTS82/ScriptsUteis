# Caminho raiz do projeto
$projectPath = "C:\dev\SPFXButterfly"
$solutionName = "CantinaV12"

# Pastas principais para listar (relativas ao projeto)
$foldersToList = @("src")

# Arquivo de saída
$outputFile = "./estrutura_simplificada.txt"

# Itens a ignorar
$exceptions = @("node_modules", "bin", "obj", ".git", ".vs", "dist", "temp", ".DS_Store")
# Extensões de arquivos que devem ser ignoradas (sem distinguir maiúsculas/minúsculas)
$excludedExtensions = @(".exe", ".zip")

# Descrições com base em caminhos relativos a partir do root (ex: "src\Services\Externals")
$folderDescriptions = @{
    "src\webparts"           = "Local onde os componentes de webparts são criados"
    "src\Models"             = "Modelos de dados utilizados no sistema"
    "src\ViewModels"         = "Camada de ViewModels, atualmente vazia"
    "src\Views"              = "Interfaces do usuário"
    "src\Resources"          = "Estilos, cores e recursos visuais"
    "src\Services\Externals" = "Serviços externos: Firebase, WhatsApp, CSV, XLSX"
    "src\Services\Internals" = "Serviços internos: Pedidos, Produtos, Configurações"
}

# Remove arquivo antigo se existir
if (Test-Path $outputFile) {
    Remove-Item $outputFile
}

# Cabeçalho
Add-Content $outputFile $solutionName
Add-Content $outputFile "│"

function Is-Excluded {
    param([string]$name)
    return $exceptions -contains $name
}

function List-FolderContent {
    param(
        [string]$path,
        [int]$indentLevel,
        [string]$relativePath
    )

    $indent = "│   " * $indentLevel

    # Pastas
    $dirs = Get-ChildItem -Path $path -Directory | Where-Object { -not (Is-Excluded $_.Name) } | Sort-Object Name
    $lastDir = $dirs.Count - 1

    for ($i = 0; $i -lt $dirs.Count; $i++) {
        $dir = $dirs[$i]
        $prefix = if ($i -eq $lastDir) { "└──" } else { "├──" }

        $fullRelative = Join-Path $relativePath $dir.Name
        $desc = $folderDescriptions[$fullRelative]
        $line = "$indent$prefix $($dir.Name)"
        if ($desc) { $line += "        ($desc)" }

        Add-Content $outputFile $line

        List-FolderContent -path $dir.FullName -indentLevel ($indentLevel + 1) -relativePath $fullRelative
    }

    # Arquivos
    $files = Get-ChildItem -Path $path -File | Where-Object {
    -not (Is-Excluded $_.Name) -and (-not ($excludedExtensions -contains $_.Extension.ToLower()))
} | Sort-Object Name
    $lastFile = $files.Count - 1

    for ($i = 0; $i -lt $files.Count; $i++) {
        $prefix = if ($i -eq $lastFile) { "└──" } else { "├──" }
        Add-Content $outputFile "$indent$prefix $($files[$i].Name)"
    }
}

# Loop nas pastas principais
foreach ($folder in $foldersToList) {
    $fullPath = Join-Path $projectPath $folder

    if (-Not (Test-Path $fullPath)) {
        Add-Content $outputFile "├── $folder (pasta não encontrada)"
        Add-Content $outputFile "│"
        continue
    }

    $desc = $folderDescriptions[$folder]
    $line = "├── $folder"
    if ($desc) { $line += "           $desc" }
    Add-Content $outputFile $line

    List-FolderContent -path $fullPath -indentLevel 1 -relativePath $folder
    Add-Content $outputFile "│"
}

# Arquivos da raiz do projeto
$rootFiles = Get-ChildItem -Path $projectPath -File | Where-Object {
    $_.Extension -match "(\.xaml|\.cs|\.json|\.config|\.xml)" -and
    (-not (Is-Excluded $_.Name)) -and
    (-not ($excludedExtensions -contains $_.Extension.ToLower()))
} | Sort-Object Name

if ($rootFiles.Count -gt 0) {
    $fileNames = $rootFiles | ForEach-Object { $_.Name }
    $fileList = $fileNames -join ", "
    Add-Content $outputFile "└── Arquivos da raiz    ($fileList)"
} else {
    Add-Content $outputFile "└── Arquivos da raiz"
}

Write-Output "Estrutura simplificada gerada com sucesso: $outputFile"
