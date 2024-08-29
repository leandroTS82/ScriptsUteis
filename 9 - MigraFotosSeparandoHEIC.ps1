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
    $destinationPath = ""

    try {
        # Tenta adicionar uma propriedade personalizada usando ExifTool
        $originalFolderName = [System.IO.Path]::GetDirectoryName($file.FullName) -replace ([regex]::Escape([System.IO.Path]::GetPathRoot($file.FullName))), ""
        $metadataComment = "Migrado do Google Fotos; Pasta original: $originalFolderName"

        # Inicializa a observação de erro
        $errorObservation = ""

        try {
            # Usa ExifTool para adicionar um comentário ao arquivo
            & exiftool -Comment="$metadataComment" $file.FullName
        } catch {
            # Captura erros ao adicionar metadados
            $errorObservation += "Erro ao adicionar metadados: $_. "
        }

       
        # Verifica a extensão do arquivo e determina o caminho de destino
        if ($file.Extension -ieq ".HEIC") {
            $specificExtensionDirectory = [System.IO.Path]::Combine($tempGFotosDirectory, "HEIC")
        } elseif ($file.Extension -ieq ".json") {
            $specificExtensionDirectory = [System.IO.Path]::Combine($tempGFotosDirectory, "JSON")
        } else {
            $specificExtensionDirectory = $destinationDirectory
        }
        

        # Cria o diretório específico se não existir
        if (!(Test-Path -Path $specificExtensionDirectory)) {
            New-Item -Path $specificExtensionDirectory -ItemType Directory
        }

        # Define o caminho de destino no diretório específico
        $destinationPath = [System.IO.Path]::Combine($specificExtensionDirectory, $file.Name)

        try {
            # Move o arquivo para o caminho de destino apropriado
            Move-Item -Path $file.FullName -Destination $destinationPath -Force
        } catch {
            # Captura erros ao mover arquivos
            $errorObservation += "Erro ao mover arquivo: $_. "
        }
        
        # Atualiza a observação com mensagens de erro, se houver
        if ($errorObservation -ne "") {
            $observation = $errorObservation
        }
        
    } catch {
        $observation = "Erro inesperado: $_"
    }

    # Adiciona os caminhos dos arquivos e informações adicionais ao array
    $filePaths += [pscustomobject]@{
        SourcePath = $file.FullName
        DestinationPath = $destinationPath
        Extension = $file.Extension
        Size = $file.Length
        Observation = $observation
    }

    Write-Host "Arquivo movido: $($file.FullName) para $destinationPath"
}

# Exporta os caminhos dos arquivos para um arquivo CSV
$filePaths | Export-Csv -Path $csvPath -NoTypeInformation

Write-Host "Arquivo CSV com os caminhos dos arquivos foi criado em: $csvPath"
