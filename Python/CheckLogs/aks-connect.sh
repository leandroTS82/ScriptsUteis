#!/bin/bash

# =========================
# CONFIG (ALTERE AQUI)

# Dev - ./aks-connect.sh dev
# Staging ./aks-connect.sh staging
# Prod - ./aks-connect.sh prod
# =========================
ENVIRONMENT=${1:-dev}

# =========================
# VARIÁVEIS POR AMBIENTE
# =========================
if [ "$ENVIRONMENT" == "dev" ]; then
  SUBSCRIPTION_ID="37cb0167-980d-4c34-a310-e21475565f40"
  RESOURCE_GROUP="aks-dev-001_group"
  CLUSTER_NAME="aks-dev-001"
elif [ "$ENVIRONMENT" == "staging" ]; then
  SUBSCRIPTION_ID="SEU-STAGING-SUBSCRIPTION"
  RESOURCE_GROUP="aks-staging-001_group"
  CLUSTER_NAME="aks-staging-001"
elif [ "$ENVIRONMENT" == "prod" ]; then
  SUBSCRIPTION_ID="SEU-PROD-SUBSCRIPTION"
  RESOURCE_GROUP="aks-prod-001_group"
  CLUSTER_NAME="aks-prod-001"
else
  echo "❌ Ambiente inválido: $ENVIRONMENT"
  exit 1
fi

# =========================
# EXECUÇÃO
# =========================
echo "🌍 Ambiente: $ENVIRONMENT"
echo "📦 Subscription: $SUBSCRIPTION_ID"
echo "📁 Resource Group: $RESOURCE_GROUP"
echo "☸️ Cluster: $CLUSTER_NAME"
echo ""

# Login (caso necessário)
echo "🔐 Verificando login Azure..."
az account show > /dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "🔑 Fazendo login..."
  az login
fi

# Set subscription
echo "🔄 Setando subscription..."
az account set --subscription $SUBSCRIPTION_ID

# Get credentials (contexto AKS)
echo "📥 Obtendo credenciais do AKS..."
az aks get-credentials \
  --resource-group $RESOURCE_GROUP \
  --name $CLUSTER_NAME \
  --overwrite-existing

# Confirmar contexto
echo ""
echo "✅ Contexto atual:"
kubectl config current-context

# Listar pods
echo ""
echo "📦 Pods no namespace my-theft:"
kubectl get pods -n my-theft

echo ""
echo "🚀 Ambiente pronto!"