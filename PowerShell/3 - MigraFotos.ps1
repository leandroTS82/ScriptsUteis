# Define os diretórios de origem e destino
$sourceDirectory = "C:\Users\leand\Downloads"
$destinationDirectory = "C:\Users\leand\Pictures\iCloud Photos\Photos"
$tempGFotosDirectory = "C:\tempGFotos"
$csvPath = "$tempGFotosDirectory\file_paths_{0:yyyyMMdd_HHmmss}.csv" -f (Get-Date)

# Cria os diretórios de destino se eles não existirem
if (!(Test-Path -Path $destinationDirectory)) {
    New-Item -Path $destinationDirectory -ItemType Directory
}

if (!(Test-Path -Path $tempGFotosDirectory)) {
    New-Item -Path $tempGFotosDirectory -ItemType Directory
}

# Inicializa um array para armazenar informações de caminho de arquivos
$filePaths = @()

# Obtém todos os arquivos em pastas e subpastas do diretório de origem
$files = Get-ChildItem -Path $sourceDirectory -Recurse -File

foreach ($file in $files) {
    $observation = "Movido com sucesso"
    $destinationPath = [System.IO.Path]::Combine($destinationDirectory, $file.Name)

    try {
        # Move o arquivo para o caminho de destino apropriado
        Move-Item -Path $file.FullName -Destination $destinationPath -Force
        # Feedback de sucesso
        Write-Host "Arquivo movido: $($file.FullName) para $destinationPath" -ForegroundColor Green
    } catch {
        # Captura erros ao mover arquivos
        $observation = "Erro ao mover arquivo: $_. "
        # Feedback de erro
        Write-Host "Erro ao mover o arquivo: $($file.FullName). Erro: $_" -ForegroundColor Red
    }

    # Adiciona os caminhos dos arquivos e informações adicionais ao array
    $filePaths += [pscustomobject]@{
        SourcePath = $file.FullName
        DestinationPath = $destinationPath
        Extension = $file.Extension
        Size = $file.Length
        Observation = $observation
    }
}

# Exporta os caminhos dos arquivos para um arquivo CSV
$filePaths | Export-Csv -Path $csvPath -NoTypeInformation

Write-Host "Arquivo CSV com os caminhos dos arquivos foi criado em: $csvPath"
