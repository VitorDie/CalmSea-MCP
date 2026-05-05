# Relatório de Benchmark: 1-orion.yaml

* **Modelo:** `mistral-small3.2:24b-instruct-2506-q4_K_M`
* **Rodada:** 2
* **Status Final:** ❌ FALHA
* **HealthCheck:** Timeout: Os recursos não atingiram estabilidade no tempo previsto

## 🧠 Raciocínio do Agente
❌ Erro de Contexto: model failed to load, this may be due to resource limitations or an internal error, check ollama server logs for details (status code: 500)

## 📋 Estado Final do Namespace (teste-orion)
```
NAME                                 READY   STATUS             RESTARTS     AGE
pod/fiware-orionld-548584cdf-8pq7m   0/1     Pending            0            2m7s
pod/fiware-orionld-548584cdf-q428v   0/1     CrashLoopBackOff   4 (2s ago)   2m7s
pod/fiware-orionld-548584cdf-tjwkz   0/1     CrashLoopBackOff   4 (2s ago)   2m7s

NAME                             TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)          AGE
service/fiware-orionld-service   LoadBalancer   10.111.147.31   <pending>     1027:31728/TCP   2m7s

NAME                             READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/fiware-orionld   0/3     3            0           2m7s

NAME                                       DESIRED   CURRENT   READY   AGE
replicaset.apps/fiware-orionld-548584cdf   3         3         0       2m7s

NAME                                                     REFERENCE                   TARGETS                              MINPODS   MAXPODS   REPLICAS   AGE
horizontalpodautoscaler.autoscaling/fiware-orionld-hpa   Deployment/fiware-orionld   cpu: <unknown>/30%, memory: 4%/70%   3         15        3          2m7s
```