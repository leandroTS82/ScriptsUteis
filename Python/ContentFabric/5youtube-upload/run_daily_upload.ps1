# =====================================================
# CONFIGURACOES
# =====================================================
$ReportsDir = "C:\dev\scripts\ScriptsUteis\Python\ContentFabric\5youtube-upload\reports"
$PythonScript = "C:\dev\scripts\ScriptsUteis\Python\ContentFabric\5youtube-upload\upload_youtube.py"
$VideosDir = "C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\EnableToYoutubeUpload"

Write-Host ""
Write-Host "====================================================="
Write-Host "Localizando ultimo report de execucao..."
Write-Host "====================================================="

$lastReport = Get-ChildItem $ReportsDir -Filter "*_report.json" |
              Sort-Object Name -Descending |
              Select-Object -First 1

if (-not $lastReport) {
    Write-Host "ERRO: Nenhum report encontrado." -ForegroundColor Red
    exit 1
}

Write-Host "Report encontrado:" $lastReport.Name

# =====================================================
# LE END_TIME E CALCULA PROXIMA EXECUCAO
# =====================================================
$json = Get-Content $lastReport.FullName | ConvertFrom-Json
$endTime = [datetime]::Parse($json.end_time)
$nextRun = $endTime.AddHours(24).AddMinutes(10)

Write-Host ""
Write-Host "Ultimo upload finalizado em :" $endTime
Write-Host "Proxima execucao permitida :" $nextRun

# =====================================================
# AGUARDA ATE O HORARIO CORRETO
# =====================================================
Write-Host ""
Write-Host "Aguardando liberacao do YouTube (24h + 10min)..."

while ((Get-Date) -lt $nextRun) {
    $remaining = $nextRun - (Get-Date)
    Write-Host ("Tempo restante: {0:hh\:mm\:ss}" -f $remaining) -NoNewline "`r"
    Start-Sleep -Seconds 1
}

Write-Host ""
Write-Host "====================================================="
Write-Host "Iniciando upload_youtube.py"
Write-Host "====================================================="

python $PythonScript $VideosDir

Write-Host ""
Write-Host "Execucao finalizada."
Write-Host "Um novo report sera gerado ao final."
