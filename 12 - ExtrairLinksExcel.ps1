# Importar o módulo ImportExcel se não estiver disponível
if (-not (Get-Module -ListAvailable -Name ImportExcel)) {
    Install-Module -Name ImportExcel -Force -Scope CurrentUser
}

# Definir os caminhos do arquivo Excel e da pasta de saída
$basePath = "./ArquivoExcel"  # Diretório base onde está o arquivo Excel
$outputDir = "$basePath/files"  # Diretório onde o JSON será salvo
$excelFile = "Cronograma-Inbound-agger_Old_copia.xlsx"  # Nome do arquivo Excel

# Definir o caminho completo para o arquivo Excel
$excelPath = "$basePath/$excelFile"

# Definir a aba e a coluna específica
$sheetName = "ARTIGOS"  # Nome da aba com os dados
$columnName = "Link texto"  # Nome da coluna que contém os links

# Gerar o nome do arquivo JSON dinamicamente baseado na aba e na coluna
$jsonFileName = "${sheetName}_${columnName}_links.json"
$outputJsonPath = "$outputDir/$jsonFileName"

# Ler o conteúdo do arquivo Excel
$excelData = Import-Excel -Path $excelPath -WorksheetName $sheetName

# Verificar se a coluna existe no arquivo Excel
if (-not ($excelData | Get-Member -Name $columnName)) {
    Write-Host "A coluna '$columnName' não foi encontrada na aba '$sheetName'. Verifique o nome da coluna."
    exit
}

# Função para verificar se a célula contém um hiperlink e retornar o link ou texto
function Get-LinkOrText {
    param ($cell)

    # Se a célula for um hyperlink da fórmula Excel, retorná-lo
    if ($cell -is [string] -and $cell.Contains("HYPERLINK")) {
        # Extraindo o URL do HYPERLINK fórmula, assumindo que está no formato =HYPERLINK("url", "texto")
        $matches = [regex]::Match($cell, '"(.*?)"')
        if ($matches.Success) {
            return $matches.Groups[1].Value
        }
    }

    # Se a célula tiver um hyperlink real (não fórmula), retornar o hyperlink
    if ($cell.PSObject.Properties["Hyperlink"] -ne $null) {
        $hyperlink = $cell.PSObject.Properties["Hyperlink"].Value
        if ($hyperlink -ne $null) {
            return $hyperlink
        }
    }

    # Caso não seja um hyperlink, retornar o texto da célula
    return $cell
}

# Obter os links ou textos da coluna especificada
$links = $excelData | ForEach-Object {
    $cell = $_.$columnName
    Get-LinkOrText $cell
}

# Criar um objeto JSON a partir dos links ou textos
$jsonOutput = $links | ConvertTo-Json -Depth 1

# Verificar se a pasta de destino existe, se não, criá-la
if (-not (Test-Path -Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir
}

# Escrever o conteúdo JSON no arquivo
$jsonOutput | Out-File -FilePath $outputJsonPath -Encoding utf8

Write-Host "Arquivo JSON gerado com sucesso em $outputJsonPath"
