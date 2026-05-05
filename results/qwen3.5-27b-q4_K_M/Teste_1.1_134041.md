# Relatório de Benchmark: 1-orion.yaml

* **Modelo:** `qwen3.5:27b-q4_K_M`
* **Rodada:** 1
* **Status Final:** ❌ FALHA
* **HealthCheck:** Timeout: Os recursos não atingiram estabilidade no tempo previsto

## 🧠 Raciocínio do Agente
Executei: apply_manifest

## 📋 Estado Final do Namespace (teste-orion)
```
NAME                             READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/fiware-orionld   0/3     0            0           2m11s

NAME                                        DESIRED   CURRENT   READY   AGE
replicaset.apps/fiware-orionld-574748bb95   3         0         0       2m11s

NAME                                                     REFERENCE                   TARGETS                                     MINPODS   MAXPODS   REPLICAS   AGE
horizontalpodautoscaler.autoscaling/fiware-orionld-hpa   Deployment/fiware-orionld   cpu: <unknown>/30%, memory: <unknown>/70%   3         15        3          10m
```