# Solicita ao usuário a inserção do nome ou parte do nome do programa
$programName = Read-Host "Digite o nome ou parte do nome do programa que deseja procurar"

# Obtém todos os programas que correspondem ao critério inserido pelo usuário
$programs = Get-WmiObject -Query "SELECT * FROM Win32_Product WHERE Name LIKE '%$programName%'"

# Verifica se algum programa foi encontrado
if ($programs) {
    # Exibe a lista de programas encontrados
    Write-Host "Programas encontrados:" -ForegroundColor Cyan
    $programs | ForEach-Object { Write-Host $_.Name -ForegroundColor Green }
    
    # Solicita confirmação ao usuário antes de desinstalar
    $confirmation = Read-Host "Deseja desinstalar todos os programas encontrados? (S/N)"
    
    if ($confirmation -eq 'S') {
        # Itera sobre cada programa encontrado e o desinstala
        foreach ($program in $programs) {
            Write-Host "Desinstalando $($program.Name)..." -ForegroundColor Yellow
            $program.Uninstall() | Out-Null
            Write-Host "$($program.Name) foi desinstalado com sucesso." -ForegroundColor Green
        }
    } else {
        Write-Host "Ação cancelada pelo usuário." -ForegroundColor Red
    }
} else {
    Write-Host "Nenhum programa encontrado com o nome '$programName'." -ForegroundColor Red
}
