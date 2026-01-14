# ============================================================
# COPY FILES SMART v2.3
# ============================================================
# - Copia arquivos de múltiplas origens para destinos
# - Filtros independentes por path
# - Controle GLOBAL de subpastas com exceções
# - Ignora arquivos já existentes
# - Feedback colorido
#
# Filtros disponíveis (AND):
#   ExcludeContains = @("preview", "test")
#   Contains        = @("wordbank")
#   StartsWith      = @("WB_", "VB_")
#   EndsWith        = @("_final")
# ============================================================

Clear-Host

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " COPY FILES SMART — Processo iniciado" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================
# CONFIGURACAO GLOBAL
# ============================================================

# Comportamento padrao: NAO varrer subpastas
$IncludeSubFolders = $false

# Excecoes: apenas estes sources varrem subpastas
$SourcesWithSubfolders = @(
    "C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\Communication site - ReunioesGravadas"
)

# ============================================================
# PATH MAPPINGS
# ============================================================


$PathMappings = @(

    # =========================
    # WORD BANK
    # =========================
    @{
        Source = "C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\VideosSemJson"
        Destination = "C:\Users\leand\Desktop\wordbank"
        Extensions = @("mp4")
    },
    @{
        Source = "C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\Youtube_Upload_Faulty_File"
        Destination = "C:\Users\leand\Desktop\wordbank"
        Extensions = @("mp4")
    },
    @{
        Source = "C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\Videos"
        Destination = "C:\Users\leand\Desktop\wordbank"
        Extensions = @("mp4")
    },
    @{
        Source = "C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\Uploaded"
        Destination = "C:\Users\leand\Desktop\wordbank"
        Extensions = @("mp4")
    },
    @{
        Source = "C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\EnableToYoutubeUpload"
        Destination = "C:\Users\leand\Desktop\wordbank"
        Extensions = @("mp4")
    },
    @{
        Source = "C:\dev\scripts\ScriptsUteis\Python\Gemini\MakeVideoGemini\outputs\videos"
        Destination = "C:\Users\leand\Desktop\wordbank"
        Extensions = @("mp4")
    },

    # =========================
    # HISTORIES
    # =========================
    @{
        Source = "C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\Histories"
        Destination = "C:\Users\leand\Desktop\wordbank\Histories"
        Extensions = @("mp4")
    },
    @{
        Source = "C:\dev\scripts\ScriptsUteis\Python\Gemini\MakeHistorieMovie\outputs\videos"
        Destination = "C:\Users\leand\Desktop\wordbank\Histories"
        Extensions = @("mp4")
    },
    @{
        Source = "C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\Histories\NewHistory"
        Destination = "C:\Users\leand\Desktop\wordbank\Histories"
        Extensions = @("mp4")
    },

    # =========================
    # REUNIÕES (ÚNICO COM SUBPASTAS)
    # =========================
    @{
        Source = "C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\Communication site - ReunioesGravadas"
        Destination = "C:\Users\leand\Desktop\ReunioesGravadas"
        Extensions = @("mp4")
        EndsWith = @("_subbed")
    }
)

# ============================================================
# PROCESSAMENTO
# ============================================================

$totalFound   = 0
$totalCopied  = 0
$totalSkipped = 0

foreach ($map in $PathMappings) {

    $source = $map.Source
    $dest   = $map.Destination

    # Decide se deve varrer subpastas
    $useSubfolders = $IncludeSubFolders -or ($SourcesWithSubfolders -contains $source)

    Write-Host "--------------------------------------------------" -ForegroundColor DarkGray
    Write-Host "Origem    : $source" -ForegroundColor Yellow
    Write-Host "Destino   : $dest" -ForegroundColor Yellow
    Write-Host "Subpastas : $useSubfolders" -ForegroundColor DarkCyan

    if (-not (Test-Path $source)) {
        Write-Host "Origem nao encontrada. Pulando." -ForegroundColor Red
        continue
    }

    New-Item -ItemType Directory -Path $dest -Force | Out-Null

    $files = Get-ChildItem -Path $source -File -Recurse:$useSubfolders

    if ($map.Extensions) {
        $files = $files | Where-Object {
            $map.Extensions -contains $_.Extension.TrimStart(".").ToLower()
        }
    }

    if ($map.EndsWith) {
        $files = $files | Where-Object {
            $name = [IO.Path]::GetFileNameWithoutExtension($_.Name)
            foreach ($e in $map.EndsWith) {
                if (-not $name.EndsWith($e)) { return $false }
            }
            return $true
        }
    }

    if (-not $files) {
        Write-Host "Nenhum arquivo compativel encontrado." -ForegroundColor DarkGray
        continue
    }

    foreach ($file in $files) {

        $totalFound++
        $destFile = Join-Path $dest $file.Name

        if (Test-Path $destFile) {
            Write-Host "Ignorado (ja existe): $($file.Name)" -ForegroundColor DarkGray
            $totalSkipped++
            continue
        }

        Copy-Item $file.FullName $destFile
        Write-Host "Copiado: $($file.Name)" -ForegroundColor Green
        $totalCopied++
    }
}

# ============================================================
# RESUMO
# ============================================================

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " RESUMO FINAL" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " Encontrados : $totalFound" -ForegroundColor White
Write-Host " Copiados    : $totalCopied" -ForegroundColor Green
Write-Host " Ignorados   : $totalSkipped" -ForegroundColor Yellow
Write-Host ""
Write-Host " Processo concluido com sucesso." -ForegroundColor Cyan
Write-Host ""
