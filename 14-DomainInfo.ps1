# Define o domínio como uma variável de entrada
$domain = "butterflygrowth.com.br"

# Função para obter informações de DNS MX do domínio
function Get-MXRecords($domain) {
    try {
        $mxRecords = (Resolve-DnsName -Name $domain -Type MX).NameExchange
        return $mxRecords
    } catch {
        Write-Output "Erro ao obter os registros MX para o domínio: $domain"
        return $null
    }
}

# Função para obter registros TXT (SPF, DKIM, DMARC)
function Get-TXTRecords($domain) {
    try {
        $txtRecords = (Resolve-DnsName -Name $domain -Type TXT).Strings
        return $txtRecords
    } catch {
        Write-Output "Erro ao obter os registros TXT para o domínio: $domain"
        return $null
    }
}

# Função para obter o registro A (IPv4)
function Get-ARecord($domain) {
    try {
        $aRecord = (Resolve-DnsName -Name $domain -Type A).IPAddress
        return $aRecord
    } catch {
        Write-Output "Erro ao obter os registros A para o domínio: $domain"
        return $null
    }
}

# Função para obter o registro AAAA (IPv6)
function Get-AAAARecord($domain) {
    try {
        $aaaaRecord = (Resolve-DnsName -Name $domain -Type AAAA).IPAddress
        return $aaaaRecord
    } catch {
        Write-Output "Erro ao obter os registros AAAA para o domínio: $domain"
        return $null
    }
}

# Função para obter registros CNAME
function Get-CNAMERecord($domain) {
    try {
        $cnameRecord = (Resolve-DnsName -Name $domain -Type CNAME).NameHost
        return $cnameRecord
    } catch {
        Write-Output "Erro ao obter os registros CNAME para o domínio: $domain"
        return $null
    }
}

# Função para obter registros NS
function Get-NSRecords($domain) {
    try {
        $nsRecords = (Resolve-DnsName -Name $domain -Type NS).NameHost
        return $nsRecords
    } catch {
        Write-Output "Erro ao obter os registros NS para o domínio: $domain"
        return $null
    }
}

# Função para obter registros SOA
function Get-SOARecord($domain) {
    try {
        $soaRecord = (Resolve-DnsName -Name $domain -Type SOA)
        return $soaRecord
    } catch {
        Write-Output "Erro ao obter os registros SOA para o domínio: $domain"
        return $null
    }
}

# Função para gerar o JSON com as informações coletadas
function Generate-Json($domain, $mxRecords, $txtRecords, $aRecord, $aaaaRecord, $cnameRecord, $nsRecords, $soaRecord) {
    $data = @{

        "Domain"      = $domain
        "MXRecords"   = $mxRecords
        "ARecord"     = $aRecord
        "AAAARecord"  = $aaaaRecord
        "TXTRecords"  = $txtRecords
        "CNAMERecord" = $cnameRecord
        "NSRecords"   = $nsRecords
        "SOARecord"   = $soaRecord
    }

    return $data | ConvertTo-Json -Depth 3
}

# Define a pasta 'json' no diretório atual (./json)
$jsonFolderPath = Join-Path (Get-Location) "json"

# Verifica se a pasta 'json' existe; se não, cria a pasta
if (-not (Test-Path -Path $jsonFolderPath)) {
    New-Item -Path $jsonFolderPath -ItemType Directory
}

# Obtém os registros DNS para o domínio
$mxRecords   = Get-MXRecords $domain
$txtRecords  = Get-TXTRecords $domain
$aRecord     = Get-ARecord $domain
$aaaaRecord  = Get-AAAARecord $domain
$cnameRecord = Get-CNAMERecord $domain
$nsRecords   = Get-NSRecords $domain
$soaRecord   = Get-SOARecord $domain

# Gera o conteúdo JSON com as informações do domínio e registros DNS
$jsonContent = Generate-Json -domain $domain -mxRecords $mxRecords -txtRecords $txtRecords -aRecord $aRecord -aaaaRecord $aaaaRecord -cnameRecord $cnameRecord -nsRecords $nsRecords -soaRecord $soaRecord

# Salva o JSON em um arquivo na pasta 'json'
$jsonFilePath = Join-Path $jsonFolderPath "domain_info_$domain.json"
$jsonContent | Out-File -FilePath $jsonFilePath -Encoding UTF8

Write-Output "Arquivo JSON criado em: $jsonFilePath"