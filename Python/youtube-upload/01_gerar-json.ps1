<#
===============================================================
 Script: 01_gerar-json.ps1
 Autor: Leandro
 Finalidade:
    Ler todos os arquivos de um diretório informado e gerar,
    para cada arquivo, um JSON contendo informações básicas.

 Uso:
    Abrir PowerShell e executar:

        .\01_gerar-json.ps1 -Path "C:\meu\diretorio"

 Observações:
    - O parâmetro -Path é obrigatório.
    - Os JSONs são criados no mesmo diretório.
    - O nome dos JSONs será:
          <nome_do_arquivo>.json
    - Se o JSON já existir, ele não será recriado.
===============================================================
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$Path
)

# Validar diretório
if (-not (Test-Path $Path)) {
    Write-Host "Erro: O diretório informado não existe."
    exit
}

# Buscar arquivos
$files = Get-ChildItem -Path $Path -File

if ($files.Count -eq 0) {
    Write-Host "Nenhum arquivo encontrado no diretório."
    exit
}

foreach ($file in $files) {

    # Nome do JSON gerado
    $jsonFileName = "$($file.BaseName).json"
    $jsonFilePath = Join-Path $Path $jsonFileName

    # Se já existe, pular
    if (Test-Path $jsonFilePath) {
        Write-Host "Ignorado (já existe): $jsonFileName"
        continue
    }

    # Criar estrutura do JSON
    $obj = [PSCustomObject]@{
        FileName   = $file.Name
        FullPath   = $file.FullName
        Extension  = $file.Extension
        SizeBytes  = $file.Length
        CreatedAt  = $file.CreationTimeUtc
        ModifiedAt = $file.LastWriteTimeUtc
    }

    # Converter para JSON
    $json = $obj | ConvertTo-Json -Depth 5 -Compress

    # Salvar JSON
    Set-Content -Path $jsonFilePath -Value $json -Encoding UTF8

    Write-Host "Gerado: $jsonFileName"
}

Write-Host "Processo concluído com sucesso."
