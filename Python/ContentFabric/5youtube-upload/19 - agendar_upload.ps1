# ==========================================
# CONFIGURAÇÃO
# ==========================================
$Minutes = 265   # Altere o tempo aqui
# ==========================================

$startSchedule = (Get-Date).ToString("HH:mm:ss")
Write-Host "`nIniciando agendamento às $startSchedule..."

$seconds = [int]$Minutes * 60
Write-Host "Aguardando $Minutes minuto(s)..."

if ($seconds -gt 0) {
    for ($i = $seconds; $i -ge 0; $i--) {

        # FORÇA OS TIPOS PARA EVITAR ERRO DE FORMATAÇÃO
        $minLeft = [int]([math]::Floor($i / 60))
        $secLeft = [int]($i % 60)

        # Formatação segura
        $msg = ("Tempo restante: {0:D2}:{1:D2}" -f $minLeft, $secLeft)

        Write-Host -NoNewline "`r$msg"

        Start-Sleep -Seconds 1
    }
}

$startTime = (Get-Date).ToString("HH:mm:ss")
Write-Host "`nIniciando upload às $startTime..."

python upload_youtube.py "C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\Videos"
