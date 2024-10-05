import openpyxl
import json
import os
from datetime import datetime

# Instruções de Execução:
# 1. Certifique-se de ter o Python instalado em seu sistema. Recomenda-se a versão 3.6 ou superior.
# 2. Instale as bibliotecas necessárias usando o seguinte comando:
#    pip install openpyxl
# 3. Altere o caminho do arquivo Excel (excel_file_path) para o local onde seu arquivo está armazenado.
# 4. Execute o script. O arquivo JSON será gerado no diretório especificado.
# 5. Comando para executar: python '.\13 - extrair_links.py' ou python3 '.\13 - extrair_links.py'

# Caminho do arquivo Excel
excel_file_path = r"C:\dev\scripts\ScriptsUteis\ArquivoExcel\Cronograma-Inbound-agger.xlsx"

# Carregar o arquivo Excel
workbook = openpyxl.load_workbook(excel_file_path)
sheet = workbook["ARTIGOS"]

# Inicializar a lista para armazenar os dados
data = []

# Definir as colunas que você deseja extrair (por exemplo, ["C","I","J"])
columns_to_extract = ["C", "I", "J"]  # Defina aqui as colunas desejadas

# Função para converter datetime para string
def convert_datetime(cell_value):
    if isinstance(cell_value, datetime):
        return cell_value.isoformat()  # Converte para o formato ISO 8601
    return cell_value

# Iterar sobre as linhas da planilha, começando da segunda linha
for row_index, row in enumerate(sheet.iter_rows(min_row=2), start=2):  # Ignorar a primeira linha (cabeçalho)
    row_data = {'row': row_index}  # Adiciona o número da linha ao dicionário
    for col in columns_to_extract:
        col_index = openpyxl.utils.column_index_from_string(col) - 1  # Converter letra para índice
        cell = row[col_index]

        if cell.hyperlink:  # Verifica se a célula contém um hiperlink
            row_data[col] = cell.hyperlink.target  # Obtém o link real
        else:
            row_data[col] = convert_datetime(cell.value)  # Obtém o valor da célula e converte se necessário

    data.append(row_data)

# Caminho do diretório para salvar o JSON
output_directory = r"C:\dev\scripts\ScriptsUteis\ArquivoExcel\files"
os.makedirs(output_directory, exist_ok=True)  # Cria o diretório se não existir

# Nome do arquivo JSON baseado na aba
json_file_name = f"{sheet.title}.json"
json_file_path = os.path.join(output_directory, json_file_name)

# Gravar os dados em um arquivo JSON
with open(json_file_path, "w", encoding="utf-8") as json_file:
    json.dump(data, json_file, ensure_ascii=False, indent=4)

print(f"Arquivo JSON gerado com sucesso em {json_file_path}!")

# Nova variável com o texto a ser procurado
search_text = "https://butterflygrowth.sharepoint.com"

# Inicializar lista para armazenar os resultados encontrados
filtered_data = [item for item in data if any(search_text in str(value) for value in item.values())]

# Caminho e nome do novo arquivo JSON para os resultados filtrados
filtered_json_file_name = f"{sheet.title}_filtered.json"
filtered_json_file_path = os.path.join(output_directory, filtered_json_file_name)

# Gravar os resultados filtrados em um novo arquivo JSON
with open(filtered_json_file_path, "w", encoding="utf-8") as filtered_json_file:
    json.dump(filtered_data, filtered_json_file, ensure_ascii=False, indent=4)

print(f"Arquivo JSON filtrado gerado com sucesso em {filtered_json_file_path}!")
