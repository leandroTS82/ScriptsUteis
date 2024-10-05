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

# Definir a aba a ser lida
$sheetName = "ARTIGOS"  # Nome da aba com os dados

# Gerar o nome do arquivo JSON dinamicamente baseado na aba
$jsonFileName = "${sheetName}_dados.json"
$outputJsonPath = "$outputDir/$jsonFileName"

# Ler o conteúdo do arquivo Excel
$excelData = Import-Excel -Path $excelPath -WorksheetName $sheetName

# Verificar se a aba possui dados
if ($excelData.Count -eq 0) {
    Write-Host "A aba '$sheetName' não contém dados."
    exit
}

# Criar uma lista para armazenar os dados das células
$allCellData = @()

# Função para obter o link de uma célula se ela for um hyperlink
function Get-Hyperlink {
    param ($cell)

    # Se a célula for um objeto com um campo Hyperlink, retornar o link, senão, retornar o valor
    if ($cell.PSObject.Properties["Hyperlink"] -ne $null) {
        return $cell.PSObject.Properties["Hyperlink"].Value
    } else {
        return $cell
    }
}

# Percorrer cada linha e coletar todas as propriedades
foreach ($row in $excelData) {
    $rowData = @{}  # Criar um dicionário para armazenar os dados da linha

    # Coletar todas as propriedades e seus valores
    foreach ($property in $row.PSObject.Properties) {
        if ($property.Name -eq "Link texto") {
            # Se for a coluna "Link texto", obter o link real
            $rowData[$property.Name] = Get-Hyperlink $property.Value
        } else {
            $rowData[$property.Name] = $property.Value
        }
    }

    # Adicionar o dicionário da linha à lista de dados
    $allCellData += $rowData
}

# Criar um objeto JSON a partir de todos os dados coletados
$jsonOutput = $allCellData | ConvertTo-Json -Depth 4  # Profundidade maior para garantir que todos os níveis sejam incluídos

# Verificar se a pasta de destino existe, se não, criá-la
if (-not (Test-Path -Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir
}

# Escrever o conteúdo JSON no arquivo
$jsonOutput | Out-File -FilePath $outputJsonPath -Encoding utf8

Write-Host "Arquivo JSON gerado com sucesso em $outputJsonPath"
