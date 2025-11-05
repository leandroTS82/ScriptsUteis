# Define os caminhos dos arquivos CSV
$tempGFotosDirectory = "C:\tempGFotos"
$driversCsvPath = "$tempGFotosDirectory\DriversInfo.csv"
$machineCsvPath = "$tempGFotosDirectory\MachineInfo.csv"

# Inicia o processamento com feedback visual
Write-Host "Iniciando coleta de informações..." -ForegroundColor Cyan

# Obtém informações sobre os drivers instalados
Write-Host "Coletando informações dos drivers..." -ForegroundColor Yellow
$drivers = Get-WmiObject Win32_PnPSignedDriver | Select-Object DeviceName, DriverVersion, Manufacturer, DriverDate, Status

# Obtém informações sobre o sistema
Write-Host "Coletando informações da máquina..." -ForegroundColor Yellow
$systemInfo = Get-WmiObject Win32_ComputerSystem | Select-Object Manufacturer, Model
$biosInfo = Get-WmiObject Win32_BIOS | Select-Object SerialNumber, SMBIOSBIOSVersion
$osInfo = Get-WmiObject Win32_OperatingSystem | Select-Object Caption, OSArchitecture, Version

# Cria um objeto com as informações da máquina
$machineInfo = [PSCustomObject]@{
    Manufacturer     = $systemInfo.Manufacturer
    Model            = $systemInfo.Model
    SerialNumber     = $biosInfo.SerialNumber
    BIOSVersion      = $biosInfo.SMBIOSBIOSVersion
    OS               = $osInfo.Caption
    OSArchitecture   = $osInfo.OSArchitecture
    OSVersion        = $osInfo.Version
}

# Exporta as informações da máquina para um CSV separado
Write-Host "Exportando informações da máquina para $machineCsvPath..." -ForegroundColor Green
$machineInfo | Export-Csv -Path $machineCsvPath -NoTypeInformation

# Exporta as informações dos drivers para outro CSV
Write-Host "Exportando informações dos drivers para $driversCsvPath..." -ForegroundColor Green
$drivers | Export-Csv -Path $driversCsvPath -NoTypeInformation

# Conclusão do processo
Write-Host "Processamento concluído com sucesso!" -ForegroundColor Cyan
Write-Host "Informações dos drivers exportadas para $driversCsvPath" -ForegroundColor Green
Write-Host "Informações da máquina exportadas para $machineCsvPath" -ForegroundColor Green
