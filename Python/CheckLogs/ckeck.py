import subprocess
from groq import Groq
import os
from datetime import datetime

client = Groq(api_key="gsk_****************************")

NAMESPACE = "my-theft"
DEPLOYMENTS = [
    "allsetraplatform-be-eventhandlers",
    "allsetraplatform-be-handlers",
    "allsetraplatform-be-servicebushandlers",
]

# ============================
# Contexto do código-fonte real
# Injete os arquivos críticos aqui
# ============================
CODE_CONTEXT = """
## Arquivo crítico: AddDocumentOnZohoCommandHandler.cs
[cole o conteúdo aqui]

## Arquivo crítico: ZohoCrmIntegration.SyncTheftDocumentSubformIdsAsync
[cole o conteúdo aqui]

## Arquivo crítico: ZohoRecordBuilder.BuildWrapper
[cole o conteúdo aqui]
"""

SYSTEM_PROMPT = """
Você é um arquiteto sênior especializado em sistemas distribuídos .NET.

## Contexto do sistema
- Pipeline: EventHub → ServiceBus → Azure Function Handler → Zoho CRM
- Stack: C# .NET, EF Core, Azure Service Bus, Zoho CRM SDK
- Problemas conhecidos:
  - ZohoSubformId não sendo persistido no banco após sync com Zoho
  - Documentos duplicados sendo criados no Zoho (idempotency failure)
  - EF Core tracking conflicts: "cannot be tracked because another instance with the same key is already being tracked"
  - AutoCompleteMessages possivelmente interferindo no retry do Service Bus
  - Comportamento diferente entre LOCAL e DEV

## Código-fonte dos arquivos críticos
""" + CODE_CONTEXT + """

## Regras de análise
- Sempre correlacione logs entre os 3 deployments pelo CorrelationId/TraceId quando presente
- Foque em causas raiz, não em sintomas
- Seja específico: mencione nomes de classes, métodos e linhas quando possível
- Não dê conselhos genéricos de EF Core — analise o código real fornecido
"""


def get_logs(deployment: str, tail: int = 500) -> str:
    result = subprocess.run(
        ["kubectl", "logs", f"deployment/{deployment}", "-n", NAMESPACE, f"--tail={tail}"],
        capture_output=True, text=True, encoding="utf-8", errors="ignore"
    )
    return result.stdout


def chunk_logs(text: str, chunk_size: int = 20000, overlap: int = 500):
    """Divide logs em chunks com overlap para não perder contexto entre partes."""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


def analyze_chunk(logs_by_deployment: dict, chunk_index: int, total_chunks: int) -> str:
    combined = ""
    for dep, log in logs_by_deployment.items():
        combined += f"\n\n=== {dep} ===\n{log}"

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",  # modelo válido no Groq
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"""
Analise os logs abaixo (parte {chunk_index + 1} de {total_chunks}).

## Seções obrigatórias

### 1. Erros e Exceções
- Liste todos os erros, com timestamp e deployment de origem
- Destaque EF Core tracking conflicts
- Destaque falhas de persistência

### 2. Análise de Idempotência
- O mesmo documento está sendo processado múltiplas vezes?
- ZohoSubformId está sendo retornado pelo Zoho mas não salvo?
- Há CREATE onde deveria haver UPDATE?

### 3. Análise de Persistência
- SaveChanges está sendo chamado após atualizar ZohoSubformId?
- Entidades estão sendo carregadas com AsNoTracking onde não deveriam?

### 4. Correlação entre Deployments
- Há mensagens aparecendo em múltiplos deployments indicando reprocessamento?
- Service Bus está fazendo retry após falha sem AutoComplete?

### 5. Hipótese de Causa Raiz
Rankeadas por probabilidade — seja específico com classe e método.

### 6. Correções Concretas
Mostre o diff do código a corrigir, não apenas descrição.

## Logs:
{combined[:25000]}
"""}
        ],
        max_tokens=4000,
        temperature=0.1  # baixa temperatura para análise técnica
    )
    return response.choices[0].message.content


# ============================
# Execução principal
# ============================
timestamp = datetime.now().strftime("%Y%m%d_%H%M")

all_logs = {dep: get_logs(dep) for dep in DEPLOYMENTS}

# Salva logs brutos por deployment
for dep, logs in all_logs.items():
    with open(f"logs_{dep}_{timestamp}.txt", "w", encoding="utf-8") as f:
        f.write(logs)

# Análise combinada
analysis = analyze_chunk(all_logs, 0, 1)

md_filename = f"analysis_{timestamp}.md"
with open(md_filename, "w", encoding="utf-8") as f:
    f.write(f"# Análise de Logs — {timestamp}\n\n")
    for dep in DEPLOYMENTS:
        f.write(f"## Deployment: {dep}\n")
        f.write(f"Linhas capturadas: {len(all_logs[dep].splitlines())}\n\n")
    f.write("---\n\n")
    f.write(analysis)

print(f"\n✅ Análise salva em: {md_filename}")
for dep in DEPLOYMENTS:
    print(f"✅ Log bruto: logs_{dep}_{timestamp}.txt")