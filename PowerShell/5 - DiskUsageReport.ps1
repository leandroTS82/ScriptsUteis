# Define o caminho do diretório temporário e do arquivo CSV de saída
$tempGFotosDirectory = "C:\tempGFotos"
if (-not (Test-Path $tempGFotosDirectory)) {
    New-Item -Path $tempGFotosDirectory -ItemType Directory | Out-Null
    Write-Host "Diretório $tempGFotosDirectory criado." -ForegroundColor Green
}

$outputCsv = "$tempGFotosDirectory\DiskUsageReport_{0:yyyyMMdd_HHmmss}.csv" -f (Get-Date)

# Função para obter o tamanho de um diretório
function Get-DirectorySize {
    param (
        [string]$Path
    )
    $size = 0
    $items = Get-ChildItem -Path $Path -Recurse -Force -ErrorAction SilentlyContinue
    foreach ($item in $items) {
        if ($item -is [System.IO.FileInfo]) {
            $size += $item.Length
        }
    }
    return [math]::round($size / 1MB, 2)
}

# Obtém todos os diretórios na unidade C
Write-Host "Obtendo diretórios na unidade C..." -ForegroundColor Yellow
$directories = Get-ChildItem -Path "C:\" -Directory -Recurse -Force -ErrorAction SilentlyContinue

# Cria uma lista para armazenar os resultados
$results = @()

Write-Host "Calculando o tamanho dos diretórios..." -ForegroundColor Yellow
foreach ($dir in $directories) {
    $size = Get-DirectorySize -Path $dir.FullName
    if ($size -gt 0) {
        $results += [PSCustomObject]@{
            Path = $dir.FullName
            Name = $dir.Name
            SizeInMB = $size
        }
    }
}

# Ordena os resultados pelo tamanho em ordem decrescente
$results = $results | Sort-Object -Property SizeInMB -Descending

# Exporta os resultados para o arquivo CSV
$results | Export-Csv -Path $outputCsv -NoTypeInformation -Encoding UTF8

Write-Host "Relatório gerado em $outputCsv" -ForegroundColor Green
