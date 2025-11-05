# ==============================================
# Script: Disable-HighCPU-Services.ps1
# Autor: Leandro (ajuste conforme necessário)
# Descrição: Desativa serviços com alto consumo de CPU.
# ==============================================

# Função auxiliar para desativar serviços com segurança
function Disable-ServiceSafely {
    param (
        [Parameter(Mandatory = $true)]
        [string]$ServiceName
    )

    try {
        $service = Get-Service -Name $ServiceName -ErrorAction Stop
        if ($service.Status -ne 'Stopped') {
            Write-Host "Parando serviço: $ServiceName..." -ForegroundColor Yellow
            Stop-Service -Name $ServiceName -Force -ErrorAction Stop
        }

        Set-Service -Name $ServiceName -StartupType Disabled
        Write-Host "Serviço '$ServiceName' desativado com sucesso." -ForegroundColor Green
    }
    catch {
        Write-Host "Serviço '$ServiceName' não encontrado ou erro ao modificar." -ForegroundColor Red
    }
}

Write-Host "==============================" -ForegroundColor Cyan
Write-Host "Desativando serviços de alto uso de CPU..." -ForegroundColor Cyan
Write-Host "==============================" -ForegroundColor Cyan

# Lista de serviços para desativar
$servicesToDisable = @(
    "SysMain",                          # Superfetch / SysMain
    "DiagTrack",                        # Connected User Experiences and Telemetry
    "WSearch",                          # Windows Search (opcional)
    "TopazOFDService",                  # Topaz OFD Protection Module (ajuste se o nome real for diferente)
    "TopazSigPlus",                     # Topaz signature service
    "MapsBroker"                        # Serviço de mapas offline (raramente usado)
)

foreach ($svc in $servicesToDisable) {
    Disable-ServiceSafely -ServiceName $svc
}

Write-Host "`nOperação concluída. Recomenda-se reiniciar o computador." -ForegroundColor Cyan
