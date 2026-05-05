# Relatório de Benchmark: 4-vllm.yaml

* **Modelo:** `qwen3.5:27b-q4_K_M`
* **Rodada:** 1
* **Status Final:** ❌ FALHA
* **HealthCheck:** Falha Crítica no Pod vllm-gemma-deployment-85f5f8b94-cnfpq: CrashLoopBackOff

## 🧠 Raciocínio do Agente
Executei: list_resources

## 📋 Estado Final do Namespace (teste-vllm)
```
NAME                                        READY   STATUS             RESTARTS      AGE
pod/vllm-gemma-deployment-85f5f8b94-cnfpq   0/1     CrashLoopBackOff   3 (49s ago)   83s

NAME                                    READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/vllm-gemma-deployment   0/1     1            0           83s

NAME                                              DESIRED   CURRENT   READY   AGE
replicaset.apps/vllm-gemma-deployment-85f5f8b94   1         1         0       83s
```