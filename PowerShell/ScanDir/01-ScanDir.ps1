$rootDirectory = "C:\dev\scripts\ScriptsUteis\Python\ContentFabric\GroqIA_WordBank"
$outputFile    = ".\files\GroqIA_WordBank.txt"

# Descricao do conteudo do arquivo de saída
$outputDescription = @"
Este arquivo contem:
1. Estrutura completa de diretorios e arquivos do projeto.
2. Conteudo de todos os arquivos permitidos.
Utilize-o para analise de codigo, auditoria ou documentacao do projeto.
"@

# Itens (pastas/arquivos) a ignorar por nome OU parte do caminho
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
    "Migrations",
    "Class1.cs",
    "certificates",
    "Resources",
    "Usings.cs",
    "data"
)

# Extensoes a ignorar
$exceptionsExtensions = @(
    ".png",".jpg",".jpeg",".gif",".ico",
    ".exe",".dll",".pdb",
    ".zip",".rar",".7z",
    ".db",".mdf",".ldf",
    ".pdf",".mp4",".http",".user",".csproj",".sln"
)

# Mostrar arquivos na arvore (true = lista arquivos; false = so diretorios)
$showFiles = $true

# Pastas a incluir (nome exato, sem considerar maiúsculas/minúsculas)
$onlyFolders = @()  # Ex: @("Pasta1","Pasta2")

# Extensões a incluir (com ponto e minúsculas)
$onlyExtensions = @() # Ex: @(".docx",".txt")

# --------- Helpers ---------
function Should-ExcludePath {
    param([string]$path, [string[]]$terms)
    foreach ($t in $terms) {
        if ($path -like "*$t*") { return $true }
    }
    return $false
}

function Should-IncludePath {
    param([string]$path, [string[]]$folders, [string[]]$exts)

    if (($folders.Count -eq 0) -and ($exts.Count -eq 0)) { return $true }

    $pathLower = $path.ToLower()
    $pathMatch = $false
    $extMatch  = $false

    foreach ($f in $folders) {
        $folderLower = $f.ToLower()
        if ($pathLower -match "[\\/]$folderLower([\\/]|$)") { 
            $pathMatch = $true
            break 
        }
    }

    $extension = [System.IO.Path]::GetExtension($path).ToLower()
    if ($exts -contains $extension) { $extMatch = $true }

    return ($pathMatch -or $extMatch)
}

function List-FolderContent {
    param(
        [string]$path,
        [int]$indentLevel = 0
    )

    $indent = ("|   " * $indentLevel)

    # Pastas (respeita exclusões, mas percorre todas)
    $dirs = Get-ChildItem -Path $path -Directory -ErrorAction SilentlyContinue |
            Where-Object { -not (Should-ExcludePath -path $_.FullName -terms $exceptions) } |
            Sort-Object Name

    foreach ($dir in $dirs) {
        $shouldShow = $false

        if ($onlyFolders.Count -gt 0) {
            # Se houver pastas na lista, mostra se a própria pasta ou algo dentro dela bate
            $shouldShow = (Should-IncludePath -path $dir.FullName -folders $onlyFolders -exts $onlyExtensions) -or
                          (Get-ChildItem -Path $dir.FullName -Recurse -File -ErrorAction SilentlyContinue |
                           Where-Object { Should-IncludePath -path $_.FullName -folders $onlyFolders -exts $onlyExtensions } |
                           Select-Object -First 1)
        }
        elseif ($onlyExtensions.Count -gt 0) {
            # Só mostra se houver arquivo com extensão desejada dentro
            $shouldShow = (Get-ChildItem -Path $dir.FullName -Recurse -File -ErrorAction SilentlyContinue |
                           Where-Object { Should-IncludePath -path $_.FullName -folders $onlyFolders -exts $onlyExtensions } |
                           Select-Object -First 1)
        }
        else {
            # Sem filtros → mostra tudo (respeitando exclusões)
            $shouldShow = $true
        }

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
                    (Should-IncludePath -path $_.FullName -folders $onlyFolders -exts $onlyExtensions)
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
        return $full.Substring($root.Length).TrimStart('\','/')
    }
    return $full
}

# --------- Scanner principal ---------
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
    Add-Content -Path $outputFile -Value "`r`nCONTEUDO DOS ARQUIVOS (filtrados):`r`n"

    Get-ChildItem -Path $rootDirectory -Recurse -File -ErrorAction SilentlyContinue |
    ForEach-Object {
        $filePath = $_.FullName

        if ([IO.Path]::GetFullPath($filePath) -eq [IO.Path]::GetFullPath($outputFile)) { return }

        if (Should-ExcludePath -path $filePath -terms $exceptions) { return }
        if ($exceptionsExtensions -contains $_.Extension.ToLower()) { return }
        if (-not (Should-IncludePath -path $filePath -folders $onlyFolders -exts $onlyExtensions)) { return }

        $relativePath = Get-RelativePathSafe -root $rootDirectory -full $filePath

        try {
            $fileContent = Get-Content -Path $filePath -ErrorAction Stop
            Add-Content -Path $outputFile -Value "Arquivo: $relativePath"
            Add-Content -Path $outputFile -Value "-----------------------------"
            Add-Content -Path $outputFile -Value $fileContent
            Add-Content -Path $outputFile -Value "`r`n"
        }
        catch {
            Write-Warning "Nao foi possível ler o arquivo: $relativePath"
            Add-Content -Path $outputFile -Value "Arquivo: $relativePath"
            Add-Content -Path $outputFile -Value "-----------------------------"
            Add-Content -Path $outputFile -Value "[ERRO AO LER O ARQUIVO]"
            Add-Content -Path $outputFile -Value "`r`n"
        }
    }

    Write-Host "Scan completo! O conteudo foi salvo em $outputFile"
}

ScanProject -rootDirectory $rootDirectory -outputFile $outputFile -outputDescription $outputDescription -exceptions $exceptions -exceptionsExtensions $exceptionsExtensions
