import requests
import re

# ==========================================================
# CONFIG
# ==========================================================

PESSOAS_URL = "https://plataforma.bigdatacorp.com.br/pessoas"
COMPANIES_URL = "https://bigboost.bigdatacorp.com.br/companies"

PATH_TOKEN = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos\Tokens\bigDataCorpToken.txt"


# ==========================================================
# TOKEN
# ==========================================================

def load_token(path=PATH_TOKEN):
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        print("Arquivo de token não encontrado:", path)
        exit()


TOKEN = load_token()


# ==========================================================
# HELPERS
# ==========================================================

def normalize_document(doc: str) -> str:
    return re.sub(r"\D", "", doc)


def is_cpf(doc: str) -> bool:
    return len(doc) == 11


def is_cnpj(doc: str) -> bool:
    return len(doc) == 14


def get_document_type(doc: str):

    if is_cpf(doc):
        return "CPF"

    if is_cnpj(doc):
        return "CNPJ"

    return None


def get_url_by_document(doc: str):

    if is_cpf(doc):
        return PESSOAS_URL

    return COMPANIES_URL


# ==========================================================
# DATASETS
# ==========================================================

def get_basic_datasets(doc):

    if is_cpf(doc):
        return "basic_data"

    return "basic_data,relationships.limit(10)"


def get_extended_datasets(doc):

    if is_cpf(doc):

        return (
            "basic_data,emails,phones,addresses,"
            "government_debtors,indebtedness_question"
        )

    return "basic_data,relationships.limit(10)"


# ==========================================================
# API
# ==========================================================

def get_headers():
    return {
        "Content-Type": "application/json",
        "Timeout": "45"
    }


def build_payload(datasets: str, document: str):

    return {
        "Datasets": datasets,
        "q": f"doc{{{document}}}",
        "AccessToken": TOKEN
    }


def call_api(url: str, payload: dict):

    response = requests.post(url, json=payload, headers=get_headers())

    if response.status_code != 200:
        print("Erro API:", response.status_code)
        print(response.text)
        return None

    return response.json()


def query_basic_data(document):

    url = get_url_by_document(document)

    datasets = get_basic_datasets(document)

    payload = build_payload(datasets, document)

    return call_api(url, payload)


def query_extended_data(document):

    url = get_url_by_document(document)

    datasets = get_extended_datasets(document)

    payload = build_payload(datasets, document)

    return call_api(url, payload)


# ==========================================================
# EXTRACTORS
# ==========================================================

def extract_result(data):

    if not data:
        return None

    results = data.get("Result", [])

    if not results:
        return None

    return results[0]


def extract_basic_data(result):
    return result.get("BasicData", {})


def extract_relationships(result):

    rel = result.get("Relationships", {})

    return rel.get("Relationships", [])


def extract_emails(result):
    return result.get("Emails", [])


def extract_phones(result):
    return result.get("Phones", [])


def extract_addresses(result):
    return result.get("Addresses", [])


def extract_debts(result):
    return result.get("GovernmentDebtors")


# ==========================================================
# PRINTERS
# ==========================================================

def print_title(title):

    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


# ----------------------------------------------------------
# CPF OUTPUT
# ----------------------------------------------------------

def print_basic_person(basic):

    print_title("INFORMAÇÕES BÁSICAS")

    print("Nome:", basic.get("Name"))
    print("CPF:", basic.get("TaxIdNumber"))
    print("Sexo:", basic.get("Gender"))
    print("Nascimento:", basic.get("BirthDate"))
    print("Idade:", basic.get("Age"))
    print("Signo:", basic.get("ZodiacSign"))
    print("Situação CPF:", basic.get("TaxIdStatus"))
    print("Estado Fiscal:", basic.get("TaxIdFiscalRegion"))
    print("Mãe:", basic.get("MotherName"))


def print_emails(emails):

    if not emails:
        return

    print_title("EMAILS")

    for email in emails:
        print("-", email.get("EmailAddress"))


def print_phones(phones):

    if not phones:
        return

    print_title("TELEFONES")

    for phone in phones:

        number = f"+{phone['CountryCode']} ({phone['AreaCode']}) {phone['Number']}"

        carrier = phone.get("CurrentCarrier", "")

        print("-", number, "-", carrier)


def print_addresses(addresses):

    if not addresses:
        return

    print_title("ENDEREÇOS")

    for a in addresses:

        address = f"{a.get('AddressMain')}, {a.get('Number')}"

        city = a.get("City")
        state = a.get("State")

        print("-", address, "-", city, "/", state)


def print_debts(debts):

    if not debts:
        return

    print_title("DÍVIDAS FEDERAIS")

    print("Total dívida:", debts.get("TotalDebtValue"))

    for d in debts.get("Debts", []):

        print(
            "-",
            d.get("DebtOrigin"),
            "| valor:",
            d.get("ConsolidatedValue"),
            "| situação:",
            d.get("RegistrationSituation")
        )


# ----------------------------------------------------------
# CNPJ OUTPUT
# ----------------------------------------------------------

def print_basic_company(basic):

    print_title("DADOS DA EMPRESA")

    print("Razão Social:", basic.get("OfficialName"))
    print("Nome Fantasia:", basic.get("TradeName"))
    print("CNPJ:", basic.get("TaxIdNumber"))
    print("Status:", basic.get("TaxIdStatus"))
    print("Fundação:", basic.get("FoundedDate"))
    print("Regime:", basic.get("TaxRegime"))
    print("Tipo:", basic.get("CompanyType_ReceitaFederal"))


def print_activities(basic):

    activities = basic.get("Activities", [])

    if not activities:
        return

    print_title("ATIVIDADES (CNAE)")

    for a in activities:

        tipo = "PRINCIPAL" if a.get("IsMain") else "SECUNDÁRIA"

        print(
            tipo,
            "|",
            a.get("Code"),
            "|",
            a.get("Activity")
        )


def print_relationships(relationships):

    if not relationships:
        return

    print_title("RELACIONAMENTOS / SÓCIOS")

    for r in relationships:

        print(
            "-",
            r.get("RelatedEntityName"),
            "|",
            r.get("RelationshipType"),
            "|",
            r.get("RelatedEntityTaxIdNumber")
        )


# ==========================================================
# FLOWS
# ==========================================================

def process_cpf(document):

    basic_response = query_basic_data(document)

    result = extract_result(basic_response)

    if not result:
        print("Nenhum resultado encontrado.")
        return

    basic = extract_basic_data(result)

    print_basic_person(basic)

    if not ask_for_extended():
        return

    extended = query_extended_data(document)

    result = extract_result(extended)

    print_emails(extract_emails(result))
    print_phones(extract_phones(result))
    print_addresses(extract_addresses(result))
    print_debts(extract_debts(result))


def process_cnpj(document):

    response = query_basic_data(document)

    result = extract_result(response)

    if not result:
        print("Nenhum resultado encontrado.")
        return

    basic = extract_basic_data(result)

    relationships = extract_relationships(result)

    print_basic_company(basic)

    print_activities(basic)

    print_relationships(relationships)


# ==========================================================
# UX
# ==========================================================

def ask_for_extended():

    answer = input("\nConsultar dados completos? (s/n): ")

    return answer.lower() == "s"


# ==========================================================
# RUNNER
# ==========================================================

def run(document):

    doc_type = get_document_type(document)

    if not doc_type:
        print("Documento inválido.")
        return

    if doc_type == "CPF":
        process_cpf(document)

    if doc_type == "CNPJ":
        process_cnpj(document)


# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":

    doc = input("Digite CPF ou CNPJ: ")

    doc = normalize_document(doc)

    run(doc)