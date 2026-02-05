# allsetra-admin-portal-backend
# allsetra-platform-backend"

$rootDirectory = "C:\Dev\AllSetra\allsetra-platform-backend"
$outputFile = ".\files\allsetra-platform-backend.txt"

$selectedFiles = @() 
$onlyFolders = @()

# Descricao do conteudo do arquivo de saída
$outputDescription = @"
"@

# Exclusões por nome/pasta
$exceptions = @(
    "node_modules", "bin", ".idea", ".github", "Properties", "obj", ".git", ".vs",
    "dist", "Migrations", "Class1.cs", "certificates", "Resources", "Usings.cs", "data"
)

# Extensões a ignorar
$exceptionsExtensions = @(
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".exe", ".dll", ".pdb", ".zip", ".rar", ".7z",
    ".db", ".mdf", ".ldf", ".pdf", ".mp4", ".http", ".user", ".csproj", ".sln"
)

$showFiles = $true

# --------- Helpers ---------

function Should-ExcludePath {
    param([string]$path, [string[]]$terms)
    foreach ($t in $terms) {
        if ($path -like "*$t*") { return $true }
    }
    return $false
}

# -------------------------
# MATCH SELECTED FILES
# -------------------------
function Match-SelectedFile {
    param(
        [string]$fileName,
        [string[]]$patterns
    )

    # selectedFiles vazio → não matcha nada!
    if ($patterns.Count -eq 0) { 
        return $false
    }

    foreach ($pattern in $patterns) {
        $p = $pattern.ToLower()
        $nameLower = $fileName.ToLower()

        # Caso: nome completo exato + extensão
        if ($p -like "*.cs") {
            if ($nameLower -eq $p) { return $true }
        }
        else {
            # Caso: contém trecho
            if ($nameLower -like "*$p*") { return $true }
        }
    }
    return $false
}

# -------------------------
# CONTROLE DE INCLUSÃO
# -------------------------
function Should-IncludePath {
    param(
        [string]$path,
        [string[]]$onlyFolders,
        [string[]]$onlyExtensions,
        [string[]]$selectedFiles
    )

    $pathLower = $path.ToLower()
    $fileName = [System.IO.Path]::GetFileName($pathLower)
    $extension = [System.IO.Path]::GetExtension($pathLower)

    # 1. selectedFiles tem prioridade máxima
    if (Match-SelectedFile -fileName $fileName -patterns $selectedFiles) {
        return $true
    }

    # 2. Controlar folders explicitamente permitidos
    foreach ($f in $onlyFolders) {
        $folderLower = $f.ToLower()
        if ($pathLower -match "[\\/]$folderLower([\\/]|$)") { 
            return $true
        }
    }

    # 3. Extensões desejadas
    if ($onlyExtensions.Count -gt 0 -and ($onlyExtensions -contains $extension)) {
        return $true
    }

    # 4. Caso especial — selectedFiles vazio e onlyFolders ativo → não incluir outros caminhos
    if ($onlyFolders.Count -gt 0 -and $selectedFiles.Count -eq 0) {
        return $false
    }

    # 5. Só libera tudo SEM QUALQUER filtro
    if ($onlyFolders.Count -eq 0 -and $onlyExtensions.Count -eq 0 -and $selectedFiles.Count -eq 0) {
        return $true
    }

    return $false
}

# -------------------------
# LISTAGEM DA ÁRVORE
# -------------------------
function List-FolderContent {
    param(
        [string]$path,
        [int]$indentLevel = 0
    )

    $indent = ("|   " * $indentLevel)

    $dirs = Get-ChildItem -Path $path -Directory -ErrorAction SilentlyContinue |
    Where-Object { -not (Should-ExcludePath -path $_.FullName -terms $exceptions) } |
    Sort-Object Name

    foreach ($dir in $dirs) {

        $shouldShow = (Should-IncludePath -path $dir.FullName -onlyFolders $onlyFolders -onlyExtensions $onlyExtensions -selectedFiles $selectedFiles)

        if ($shouldShow) {
            Add-Content -Path $outputFile -Value "$indent|-- $($dir.Name)"
        }

        List-FolderContent -path $dir.FullName -indentLevel ($indentLevel + 1)
    }

    if ($showFiles) {
        $files = Get-ChildItem -Path $path -File -ErrorAction SilentlyContinue |
        Where-Object {
            -not (Should-ExcludePath -path $_.FullName -terms $exceptions) -and
            (-not ($exceptionsExtensions -contains $_.Extension.ToLower())) -and
            (Should-IncludePath -path $_.FullName -onlyFolders $onlyFolders -onlyExtensions $onlyExtensions -selectedFiles $selectedFiles)
        } |
        Sort-Object Name

        foreach ($file in $files) {
            Add-Content -Path $outputFile -Value "$indent|-- $($file.Name)"
        }
    }
}

function Get-RelativePathSafe {
    param([string]$root, [string]$full)
    if ($full.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $full.Substring($root.Length).TrimStart('\', '/')
    }
    return $full
}

# --------- Scanner Principal ---------

function ScanProject {
    param(
        [string]$rootDirectory,
        [string]$outputFile,
        [string]$outputDescription,
        [array]$exceptions,
        [array]$exceptionsExtensions
    )

    $outDir = Split-Path -Path $outputFile -Parent
    if (-not (Test-Path $outDir)) { New-Item -Path $outDir -ItemType Directory | Out-Null }

    Set-Content -Path $outputFile -Value "" -Encoding UTF8

    Add-Content -Path $outputFile -Value "Estrutura de pastas de: $rootDirectory"
    Add-Content -Path $outputFile -Value "Gerado em: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    Add-Content -Path $outputFile -Value ""
    Add-Content -Path $outputFile -Value "Descricao:"
    Add-Content -Path $outputFile -Value $outputDescription
    Add-Content -Path $outputFile -Value "|"
    Add-Content -Path $outputFile -Value "|-- $(Split-Path $rootDirectory -Leaf)"

    List-FolderContent -path $rootDirectory -indentLevel 1

    Add-Content -Path $outputFile -Value "|"
    Add-Content -Path $outputFile -Value ("=" * 80)
    Add-Content -Path $outputFile -Value "`r`nCONTEUDO DOS ARQUIVOS:`r`n"

    Get-ChildItem -Path $rootDirectory -Recurse -File -ErrorAction SilentlyContinue |
    ForEach-Object {
        $filePath = $_.FullName

        if ([IO.Path]::GetFullPath($filePath) -eq [IO.Path]::GetFullPath($outputFile)) { return }

        if (Should-ExcludePath -path $filePath -terms $exceptions) { return }
        if ($exceptionsExtensions -contains $_.Extension.ToLower()) { return }
        if (-not (Should-IncludePath -path $filePath -onlyFolders $onlyFolders -onlyExtensions $onlyExtensions -selectedFiles $selectedFiles)) { return }

        $relativePath = Get-RelativePathSafe -root $rootDirectory -full $filePath

        try {
            $fileContent = Get-Content -Path $filePath
            Add-Content -Path $outputFile -Value "Arquivo: $relativePath"
            Add-Content -Path $outputFile -Value "-----------------------------"
            Add-Content -Path $outputFile -Value $fileContent
            Add-Content -Path $outputFile -Value "`r`n"
        }
        catch {
            Add-Content -Path $outputFile -Value "Arquivo: $relativePath"
            Add-Content -Path $outputFile -Value "-----------------------------"
            Add-Content -Path $outputFile -Value "[ERRO AO LER O ARQUIVO]"
            Add-Content -Path $outputFile -Value "`r`n"
        }
    }

    Write-Host "Scan completo! O conteudo foi salvo em $outputFile"
}

ScanProject -rootDirectory $rootDirectory -outputFile $outputFile -outputDescription $outputDescription -exceptions $exceptions -exceptionsExtensions $exceptionsExtensions
