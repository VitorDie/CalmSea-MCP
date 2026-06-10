!/usr/bin/env bash

set -euo pipefail

FILE="${1:?Uso: ./renova-default.sh caminho/do/arquivo.yaml}"
NS="default"

echo "===== ARQUIVO ALVO ====="
echo "$FILE"

test -f "$FILE" || { echo "ERRO: arquivo não encontrado: $FILE"; exit 1; }

echo
echo "===== VALIDANDO QUE O YAML NÃO USA NAMESPACE FIWARE ====="
if grep -nE '^[[:space:]]*namespace:[[:space:]]*fiware([[:space:]]|$)' "$FILE"; then
  echo
  echo "ERRO: o YAML contém namespace fiware. O script foi interrompido para evitar interferência."
  exit 1
fi

echo
echo "===== VALIDANDO QUE O YAML NÃO USA OUTRO NAMESPACE EXPLÍCITO ====="
if grep -nE '^[[:space:]]*namespace:[[:space:]]*[^[:space:]#]+' "$FILE" | grep -vE 'namespace:[[:space:]]*default([[:space:]#]|$)' ; then
  echo
  echo "ERRO: o YAML contém namespace explícito diferente de default."
  echo "Ajuste/remova o campo metadata.namespace antes de aplicar."
  exit 1
fi

echo
echo "===== BLOQUEANDO RECURSOS CLUSTER-SCOPED ====="
if grep -nE '^[[:space:]]*kind:[[:space:]]*(Namespace|ClusterRole|ClusterRoleBinding|CustomResourceDefinition|StorageClass|PersistentVolume|MutatingWebhookConfiguration|ValidatingWebhookConfiguration)([[:space:]]|$)' "$FILE"; then
  echo
  echo "ERRO: o YAML contém recurso cluster-scoped. Isso pode afetar o cluster inteiro."
  exit 1
fi

echo
echo "===== CONTEXTO KUBERNETES ATUAL ====="
kubectl config current-context

echo
echo "===== GARANTINDO QUE O NAMESPACE DEFAULT EXISTE ====="
kubectl get namespace "$NS" >/dev/null

echo
echo "===== REMOVENDO APENAS OS RECURSOS DO YAML NO NAMESPACE DEFAULT ====="
kubectl delete -n "$NS" -f "$FILE" --ignore-not-found=true || true

echo
echo "===== AGUARDANDO LIMPEZA BÁSICA ====="
sleep 3

echo
echo "===== APLICANDO YAML NO NAMESPACE DEFAULT ====="
kubectl apply -n "$NS" -f "$FILE"

echo
echo "===== RECURSOS DO YAML EM DEFAULT ====="
kubectl get -n "$NS" -f "$FILE" --ignore-not-found=true || true

echo
echo "===== PODS EM DEFAULT ====="
kubectl get pods -n "$NS" -o wide

echo
echo "===== HPA EM DEFAULT ====="
kubectl get hpa -n "$NS" 2>/dev/null || true

echo
echo "===== EVENTOS RECENTES EM DEFAULT ====="
kubectl get events -n "$NS" --sort-by=.lastTimestamp | tail -n 30