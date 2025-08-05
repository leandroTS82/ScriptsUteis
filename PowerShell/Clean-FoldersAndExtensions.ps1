# Caminho base onde a limpeza será realizada
$basePath = "C:\Dev\Temp"

# Lista de nomes de diretórios OU extensões de arquivos a serem removidos
$targets = @(
    "node_modules", "bin", "obj",
    ".git", ".vscode", ".DS_Store", ".idea", ".vs", ".cache", ".history", ".github",
    ".log", ".tmp"
)

function Clean-Targets {
    param (
        [string]$path,
        [string[]]$targets
    )

    Write-Host ""
    Write-Host "Iniciando a varredura em: $path" -ForegroundColor Cyan
    $removedCount = 0

    foreach ($target in $targets) {
        $target = $target.Trim()
        Write-Host ""
        Write-Host ("[INFO] Procurando por: {0}" -f $target) -ForegroundColor Gray

        # Extensões de arquivo (ex: .log, .tmp)
        if ($target -match "^\.\w+$") {
            $files = Get-ChildItem -Path $path -Recurse -File -Force -ErrorAction SilentlyContinue |
                Where-Object { $_.Extension -ieq $target }

            Write-Host ("[ARQUIVOS] Encontrados: {0}" -f $files.Count) -ForegroundColor Blue

            foreach ($file in $files) {
                try {
                    Remove-Item $file.FullName -Force -ErrorAction Stop
                    Write-Host ("[REMOVIDO] Arquivo: {0}" -f $file.FullName) -ForegroundColor Yellow
                    $removedCount++
                } catch {
                    Write-Host ("[ERRO] Falha ao remover arquivo: {0}" -f $file.FullName) -ForegroundColor DarkRed
                }
            }
        }

        # Diretórios com nome exato (inclusive .git, bin etc)
        $folders = Get-ChildItem -Path $path -Recurse -Directory -Force -ErrorAction SilentlyContinue |
            Where-Object { $_.Name.Trim() -ieq $target }

        Write-Host ("[PASTAS] Encontradas: {0}" -f $folders.Count) -ForegroundColor Magenta

        foreach ($folder in $folders) {
            try {
                Remove-Item $folder.FullName -Recurse -Force -ErrorAction Stop
                Write-Host ("[REMOVIDO] Diretório: {0}" -f $folder.FullName) -ForegroundColor Red
                $removedCount++
            } catch {
                Write-Host ("[ERRO] Falha ao remover diretório: {0}" -f $folder.FullName) -ForegroundColor DarkRed
            }
        }
    }

    Write-Host ""
    Write-Host ("Limpeza concluída. Total de itens removidos: {0}" -f $removedCount) -ForegroundColor Green
}

# Executa a função
Clean-Targets -path $basePath -targets $targets
