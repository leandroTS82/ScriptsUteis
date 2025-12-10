# Exemplo para esperar 15 minutos:
    # powershell -ExecutionPolicy Bypass -File run_delayed.ps1 -Minutes 15
# Exemplo para esperar 120 minutos (2 horas):
    # powershell -ExecutionPolicy Bypass -File run_delayed.ps1 -Minutes 120

pparam(
    [int]$Minutes = 0
)

$startSchedule = (Get-Date).ToString("HH:mm:ss")
Write-Host "`nIniciando agendamento às $startSchedule..."

$seconds = $Minutes * 60
Write-Host "Aguardando $Minutes minuto(s)..."

for ($i = $seconds; $i -ge 0; $i--) {
    $minLeft = [math]::Floor($i / 60)
    $secLeft = $i % 60

    $msg = "Tempo restante: {0:D2}:{1:D2}" -f $minLeft, $secLeft
    Write-Host -NoNewline "`r$msg"

    Start-Sleep -Seconds 1
}

$startTime = (Get-Date).ToString("HH:mm:ss")
Write-Host "`nIniciando upload às $startTime..."

python upload_youtube.py "C:\Users\leand\LTS - CONSULTORIA E DESENVOLVIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\Videos"
