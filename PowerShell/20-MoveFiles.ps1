# ==========================================
# CONFIGURAÇÕES
# ==========================================

# Caminhos de origem e destino
# Defina quantos pares quiser

$PathMappings = @(
    @{
        # Vídeos
        SourcePath = "C:\dev\scripts\ScriptsUteis\Python\Gemini\MakeVideoGemini\outputs\videos"
        DestinationPath = "C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\Videos"
    },
    @{
        # Audio
        SourcePath = "C:\dev\scripts\ScriptsUteis\Python\Gemini\MakeVideoGemini\outputs\audio"
        DestinationPath = "C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Audios para estudar inglês"
    },
    @{
        # Imagens
        SourcePath = "C:\dev\scripts\ScriptsUteis\Python\Gemini\MakeVideoGemini\outputs\images"
        DestinationPath = "C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\Images"
    },
    @{
        # !!!! Uploaded StartsWith: uploaded_
        #SourcePath = "C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\Videos"
        #DestinationPath = "C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\Uploaded"
    }
)

# Filtros (preencha conforme necessário)
# StartsWith → arquivos que começam com o texto definido
# Contains → arquivos que contêm o texto definido
# ExactName → nome exatamente igual
# Extension → extensão do arquivo (ex: .mp3, .wav)
#Case-insensitive garantido usando StringComparison.OrdinalIgnoreCase
# Usa OR lógico (se atender a qualquer critério, o arquivo é movido) - Se não quiser usar algum filtro, deixe a variável vazia

$StartsWith = ""     # arquivos que INICIAM com
$Contains   = ""     # arquivos que CONTÊM
$ExactName  = ""     # arquivos EXATAMENTE iguais
$Extension  = ""     # extensão do arquivo (inclua o ponto, ex: .mp3)

# Flags de controle
$IncludeSubfolders = $true    # true = percorre subpastas
$DryRun            = $false   # true = apenas simula (preview)

# Quantos arquivos mostrar no preview
$PreviewSampleSize = 10

# ==========================================
# EXECUÇÃO PARA CADA PAR ORIGEM / DESTINO
# ==========================================

foreach ($mapping in $PathMappings) {

    # Ignorar entradas incompletas ou comentadas
    if (-not $mapping.SourcePath -or -not $mapping.DestinationPath) {
        continue
    }

    $SourcePath      = $mapping.SourcePath
    $DestinationPath = $mapping.DestinationPath

    # ==========================================
    # GARANTIR DESTINO
    # ==========================================
    if (!(Test-Path $DestinationPath)) {
        New-Item -ItemType Directory -Path $DestinationPath | Out-Null
    }

    # ==========================================
    # LISTAR ARQUIVOS
    # ==========================================
    $files = if ($IncludeSubfolders) {
        Get-ChildItem -Path $SourcePath -File -Recurse
    } else {
        Get-ChildItem -Path $SourcePath -File
    }

    # ==========================================
    # FILTRAR (CASE-INSENSITIVE)
    # ==========================================
    $filteredFiles = $files | Where-Object {

        $name = $_.Name
        $ext  = $_.Extension

        # Se nenhum filtro foi informado, mover tudo
        if (-not $StartsWith -and -not $Contains -and -not $ExactName -and -not $Extension) {
            return $true
        }

        (
            ($StartsWith -and $name.StartsWith($StartsWith, [System.StringComparison]::OrdinalIgnoreCase)) -or
            ($Contains   -and $name.IndexOf($Contains, [System.StringComparison]::OrdinalIgnoreCase) -ge 0) -or
            ($ExactName  -and $name.Equals($ExactName, [System.StringComparison]::OrdinalIgnoreCase)) -or
            ($Extension  -and $ext.Equals($Extension, [System.StringComparison]::OrdinalIgnoreCase))
        )
    }

    # ==========================================
    # PREVIEW / EXECUÇÃO
    # ==========================================
    if ($DryRun) {

        Write-Host ""
        Write-Host "================ PREVIEW ================="
        Write-Host "Origem:   $SourcePath"
        Write-Host "Destino: $DestinationPath"
        Write-Host ""
        Write-Host "Total de arquivos encontrados: $($files.Count)"
        Write-Host "Total de arquivos que SERIAM movidos: $($filteredFiles.Count)"
        Write-Host ""

        if ($filteredFiles.Count -gt 0) {
            Write-Host "Exemplos de arquivos:"
            $filteredFiles |
                Select-Object -First $PreviewSampleSize |
                ForEach-Object { Write-Host " - $($_.Name)" }

            if ($filteredFiles.Count -gt $PreviewSampleSize) {
                Write-Host " ... e mais $($filteredFiles.Count - $PreviewSampleSize) arquivos."
            }
        }
        else {
            Write-Host "Nenhum arquivo corresponde aos filtros informados."
        }

        Write-Host "=========================================="
        Write-Host ""
        Write-Host "Modo PREVIEW ativo. Nenhum arquivo foi movido por que dryrun está ativado."
    }
    else {

        foreach ($file in $filteredFiles) {
            $destination = Join-Path $DestinationPath $file.Name
            Move-Item -Path $file.FullName -Destination $destination -Force
        }

        Write-Host ""
        Write-Host "Processo concluído com sucesso."
        Write-Host "Arquivos movidos: $($filteredFiles.Count)"
    }
}
