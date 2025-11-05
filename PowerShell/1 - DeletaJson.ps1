$sourceDirectory = "C:\Users\leand\Downloads"

# Verifica se o diretório existe
if (Test-Path -Path $sourceDirectory) {
    # Obtém todos os arquivos com extensão .json em todas as pastas e subpastas
    $jsonFiles = Get-ChildItem -Path $sourceDirectory -Filter *.json -Recurse

    # Deleta os arquivos
    if ($jsonFiles) {
        foreach ($file in $jsonFiles) {
            Remove-Item -Path $file.FullName -Force
            Write-Output "Arquivo deletado: $($file.FullName)"
        }
    } else {
        Write-Output "Nenhum arquivo .json encontrado no diretório $sourceDirectory."
    }
} else {
    Write-Output "O diretório $sourceDirectory não existe."
}
