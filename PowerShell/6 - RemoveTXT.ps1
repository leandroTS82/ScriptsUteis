# Define o caminho do diretório
$directoryPath = "C:\Users\leand\iCloud Photos Archive"

# Verifica se o diretório existe
if (Test-Path $directoryPath) {
    # Obtém todos os arquivos .txt no diretório e seus subdiretórios
    $txtFiles = Get-ChildItem -Path $directoryPath -Recurse -Filter *.txt

    # Remove cada arquivo .txt encontrado
    foreach ($file in $txtFiles) {
        try {
            Remove-Item -Path $file.FullName -Force
            Write-Output "Arquivo removido: $($file.FullName)"
        } catch {
            Write-Output "Erro ao remover o arquivo: $($file.FullName) - $_"
        }
    }
} else {
    Write-Output "O diretório $directoryPath não foi encontrado."
}
