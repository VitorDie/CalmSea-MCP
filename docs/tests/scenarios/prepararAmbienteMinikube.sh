for FILE in $(find . -maxdepth 1 -type f -name "*.yaml" | sed 's|^\./||' | sort -V); do
  BASE="$(basename "$FILE" .yaml)"

  case "$BASE" in
    1-orion)         NS="teste-orion" ;;
    2-frontend)      NS="teste-frontend" ;;
    3-mysql)         NS="teste-mysql" ;;
    4-vllm)          NS="teste-vllm" ;;
    5-nginx)         NS="teste-nginx" ;;
    6-selenium)      NS="teste-selenium" ;;
    7-elasticsearch) NS="teste-elasticsearch" ;;
    8-newrelic)      NS="teste-newrelic" ;;
    9-storm)         NS="teste-storm" ;;
    10-mongodb)      NS="teste-mongodb" ;;
    *)
      echo "Ignorando arquivo não mapeado: $FILE"
      continue
      ;;
  esac

  echo
  echo "========================================"
  echo "Aplicando $FILE no namespace $NS"
  echo "========================================"

  # Verifica se o namespace existe, se não, cria
  kubectl get namespace "$NS" >/dev/null 2>&1 || kubectl create namespace "$NS"

  # Remove recursos antigos e aguarda a limpeza
  kubectl delete -n "$NS" -f "$FILE" --ignore-not-found=true
  kubectl wait --for=delete pod --all -n "$NS" --timeout=120s || true

  # Aplica o novo manifesto
  kubectl apply -n "$NS" -f "$FILE"

  echo
  echo "===== Recursos em $NS ====="
  kubectl get all -n "$NS"
  kubectl get hpa -n "$NS" 2>/dev/null || true
  kubectl get events -n "$NS" --sort-by=.lastTimestamp | tail -n 20
done