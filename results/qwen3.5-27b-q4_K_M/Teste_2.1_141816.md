# Relatório de Benchmark: 2-frontend.yaml

* **Modelo:** `qwen3.5:27b-q4_K_M`
* **Rodada:** 1
* **Status Final:** ❌ FALHA
* **HealthCheck:** Falha Crítica no Pod frontend-65d44dd469-k5zmp: ImagePullBackOff

## 🧠 Raciocínio do Agente
Executei: list_resources

## 📋 Estado Final do Namespace (teste-frontend)
```
NAME                            READY   STATUS             RESTARTS   AGE
pod/frontend-65d44dd469-k5zmp   0/1     ImagePullBackOff   0          75s

NAME                       READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/frontend   0/1     1            0           75s

NAME                                  DESIRED   CURRENT   READY   AGE
replicaset.apps/frontend-65d44dd469   1         1         0       75s
```