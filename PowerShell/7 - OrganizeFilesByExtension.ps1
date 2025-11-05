# Defina os caminhos de origem e destino
$sourcePath = "C:\Users\leand\iCloud Photos Archive"
$destinationPath = "C:\Users\leand\iCloud Photos Archive\Sorted"

# Verifica se o diretório de destino existe; caso contrário, cria
if (!(Test-Path -Path $destinationPath)) {
    New-Item -ItemType Directory -Path $destinationPath
    Write-Host "Diretório de destino criado: $destinationPath" -ForegroundColor Green
}

# Obtém todos os arquivos do diretório de origem e subdiretórios
Get-ChildItem -Path $sourcePath -Recurse -File | ForEach-Object {
    $file = $_
    $extension = $file.Extension.TrimStart('.').ToUpper() # Obtém a extensão do arquivo e remove o ponto inicial
    
    # Cria o diretório de destino baseado na extensão, se não existir
    $destinationFolder = Join-Path -Path $destinationPath -ChildPath $extension
    if (!(Test-Path -Path $destinationFolder)) {
        New-Item -ItemType Directory -Path $destinationFolder
        Write-Host "Criado diretório para extensão .${extension}: $destinationFolder" -ForegroundColor Green
    }
    
    # Move o arquivo para o diretório de destino
    $destinationFile = Join-Path -Path $destinationFolder -ChildPath $file.Name
    Move-Item -Path $file.FullName -Destination $destinationFile -Force
    Write-Host "Movido: $($file.FullName) -> $($destinationFile)" -ForegroundColor Yellow
}

Write-Host "Organização de arquivos concluída!" -ForegroundColor Cyan
