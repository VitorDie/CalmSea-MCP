# Relatório de Benchmark: 4-vllm.yaml

* **Modelo:** `qwen3.5:27b-q4_K_M`
* **Rodada:** 2
* **Status Final:** ❌ FALHA
* **HealthCheck:** Falha Crítica no Pod vllm-gemma-deployment-85f5f8b94-g6797: CrashLoopBackOff

## 🧠 Raciocínio do Agente
Executei: list_resources

## 📋 Estado Final do Namespace (teste-vllm)
```
NAME                                         READY   STATUS              RESTARTS      AGE
pod/vllm-gemma-deployment-58ff779db6-mt8sq   0/1     Pending             0             13s
pod/vllm-gemma-deployment-85f5f8b94-g6797    0/1     CrashLoopBackOff    5 (61s ago)   3m54s
pod/vllm-gemma-deployment-85f5f8b94-trs5b    0/1     RunContainerError   1 (11s ago)   13s

NAME                         TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)   AGE
service/vllm-gemma-service   ClusterIP   10.104.240.204   <none>        80/TCP    13s

NAME                                    READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/vllm-gemma-deployment   0/2     1            0           3m54s

NAME                                               DESIRED   CURRENT   READY   AGE
replicaset.apps/vllm-gemma-deployment-58ff779db6   1         1         0       13s
replicaset.apps/vllm-gemma-deployment-85f5f8b94    2         2         0       3m54s
```