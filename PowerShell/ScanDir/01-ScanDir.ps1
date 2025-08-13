$rootDirectory = "C:\Dev\AllSetra\allsetra-platform-backend"
$outputFile    = ".\files\Conteudo_allsetra-platform-backend.txt"

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
    "Usings.cs"
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

# --------- Helpers ---------
function Should-ExcludePath {
    param([string]$path, [string[]]$terms)
    foreach ($t in $terms) {
        if ($path -like "*$t*") { return $true }
    }
    return $false
}

function List-FolderContent {
    param(
        [string]$path,
        [int]$indentLevel = 0
    )

    $indent = ("|   " * $indentLevel)

    # Pastas (filtra as excluídas)
    $dirs = Get-ChildItem -Path $path -Directory -ErrorAction SilentlyContinue |
            Where-Object { -not (Should-ExcludePath -path $_.FullName -terms $exceptions) } |
            Sort-Object Name

    foreach ($dir in $dirs) {
        Add-Content -Path $outputFile -Value "$indent|-- $($dir.Name)"
        List-FolderContent -path $dir.FullName -indentLevel ($indentLevel + 1)
    }

    if ($showFiles) {
        # Arquivos (filtra nome/caminho e extensoes)
        $files = Get-ChildItem -Path $path -File -ErrorAction SilentlyContinue |
                 Where-Object {
                    -not (Should-ExcludePath -path $_.FullName -terms $exceptions) -and
                    (-not ($exceptionsExtensions -contains $_.Extension.ToLower()))
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

    # Garante pasta de saída
    $outDir = Split-Path -Path $outputFile -Parent
    if (-not (Test-Path $outDir)) { New-Item -Path $outDir -ItemType Directory | Out-Null }

    # (Re)cria arquivo
    Set-Content -Path $outputFile -Value "" -Encoding UTF8

    # Cabecalho + descricao
    Add-Content -Path $outputFile -Value "Estrutura de pastas de: $rootDirectory"
    Add-Content -Path $outputFile -Value "Gerado em: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    Add-Content -Path $outputFile -Value ""
    Add-Content -Path $outputFile -Value "Descricao:"
    Add-Content -Path $outputFile -Value $outputDescription
    Add-Content -Path $outputFile -Value "|"
    Add-Content -Path $outputFile -Value "|-- $(Split-Path $rootDirectory -Leaf)"

    # 1) arvore de pastas
    List-FolderContent -path $rootDirectory -indentLevel 1
    Add-Content -Path $outputFile -Value "|"
    Add-Content -Path $outputFile -Value ("=" * 80)
    Add-Content -Path $outputFile -Value "`r`nCONTEUDO DOS ARQUIVOS (filtrados):`r`n"

    # 2) Conteudo dos arquivos
    Get-ChildItem -Path $rootDirectory -Recurse -File -ErrorAction SilentlyContinue |
    ForEach-Object {
        $filePath = $_.FullName

        # Pular o proprio arquivo de saída
        if ([IO.Path]::GetFullPath($filePath) -eq [IO.Path]::GetFullPath($outputFile)) { return }

        # Aplicar filtros
        if (Should-ExcludePath -path $filePath -terms $exceptions) { return }
        if ($exceptionsExtensions -contains $_.Extension.ToLower()) { return }

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
