# Define o diretório de saída
$directoryPath = "./files"

# Verifica se o diretório existe, senão, cria
if (!(Test-Path -Path $directoryPath)) {
    New-Item -ItemType Directory -Path $directoryPath
}

# Obtém informações dos programas instalados no sistema
$installedPrograms = Get-ItemProperty -Path "HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*" `
                    , "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*" |
                    Select-Object DisplayName, DisplayVersion, Publisher, InstallDate |
                    Where-Object { $_.DisplayName -and $_.DisplayVersion }

# Cria um objeto JSON a partir das informações obtidas
$jsonOutput = $installedPrograms | ConvertTo-Json -Depth 3

# Salva o JSON no arquivo
$outputFile = Join-Path $directoryPath "installed_programs.json"
$jsonOutput | Out-File -FilePath $outputFile -Encoding utf8

Write-Host "Informações dos programas instalados salvas em $outputFile"