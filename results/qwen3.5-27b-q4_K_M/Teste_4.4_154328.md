# Relatório de Benchmark: 4-vllm.yaml

* **Modelo:** `qwen3.5:27b-q4_K_M`
* **Rodada:** 4
* **Status Final:** ❌ FALHA
* **HealthCheck:** Falha Crítica no Pod vllm-gemma-deployment-85f5f8b94-hgkk9: CrashLoopBackOff

## 🧠 Raciocínio do Agente


## 📋 Estado Final do Namespace (teste-vllm)
```
NAME                                        READY   STATUS             RESTARTS       AGE
pod/vllm-gemma-deployment-85f5f8b94-hgkk9   0/1     CrashLoopBackOff   7 (3m4s ago)   14m

NAME                                    READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/vllm-gemma-deployment   0/1     1            0           14m

NAME                                              DESIRED   CURRENT   READY   AGE
replicaset.apps/vllm-gemma-deployment-85f5f8b94   1         1         0       14m
```