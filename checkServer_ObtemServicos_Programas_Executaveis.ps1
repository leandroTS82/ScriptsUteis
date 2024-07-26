$searchPath = "C:\"
$outputCsv = "C:\Temp\Servicos_e_programas_instalados.csv"

# Cria um array para armazenar as informações dos serviços e programas
$infoData = @()

# Consulta todos os serviços instalados
Write-Output "Consultando todos os serviços instalados..."
$services = Get-WmiObject -Class Win32_Service

foreach ($service in $services) {
    $serviceInfo = New-Object PSObject -Property @{
        Type = 'Serviço'
        Name = $service.Name
        Path = $service.PathName
        Version = $null
        Observations = $null
        Status = $service.State
    }

    # Tenta obter a versão do serviço
    try {
        $version = (Get-Command $service.PathName -ErrorAction Stop).FileVersionInfo.FileVersion
        $serviceInfo.Version = $version
    } catch {
        $serviceInfo.Observations = "Não foi possível obter a versão."
    }

    # Adiciona as informações do serviço ao array
    $infoData += $serviceInfo

    # Exibe uma mensagem na tela a cada 10 serviços para monitorar o andamento
    if (($services.IndexOf($service) + 1) % 10 -eq 0) {
        Write-Output "Processado $($services.IndexOf($service) + 1) serviços..."
    }
}

# Consulta programas instalados procurando por executáveis
Write-Output "Procurando por arquivos executáveis em todo o sistema..."
$executableFiles = Get-ChildItem -Path $searchPath -Recurse -Filter *.exe -ErrorAction SilentlyContinue

foreach ($file in $executableFiles) {
    $programInfo = New-Object PSObject -Property @{
        Type = 'Executável'
        Name = $file.Name
        Path = $file.FullName
        Version = $null
        Observations = $null
        Status = "N/A"
    }

    # Tenta obter a versão do executável
    try {
        $version = (Get-Command $file.FullName -ErrorAction Stop).FileVersionInfo.FileVersion
        $programInfo.Version = $version
    } catch {
        $programInfo.Observations = "Não foi possível obter a versão."
    }

    # Adiciona as informações do programa ao array
    $infoData += $programInfo

    # Exibe uma mensagem na tela a cada 100 arquivos para monitorar o andamento
    if (($executableFiles.IndexOf($file) + 1) % 100 -eq 0) {
        Write-Output "Processados $($executableFiles.IndexOf($file) + 1) arquivos executáveis..."
    }
}

# Exporta as informações para o arquivo CSV
Write-Output "Gerando arquivo CSV..."
$infoData | Export-Csv -Path $outputCsv -NoTypeInformation

Write-Output "Arquivo CSV gerado em: $outputCsv"
