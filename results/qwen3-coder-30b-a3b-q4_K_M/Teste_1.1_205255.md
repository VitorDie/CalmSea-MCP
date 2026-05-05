# Relatório de Benchmark: 1-orion.yaml

* **Modelo:** `qwen3-coder:30b-a3b-q4_K_M`
* **Rodada:** 1
* **Status Final:** ❌ FALHA
* **HealthCheck:** Falha Crítica no Pod fiware-orionld-548584cdf-q2dmk: CrashLoopBackOff

## 🧠 Raciocínio do Agente
Executei: get_resource_details

## 📋 Estado Final do Namespace (teste-orion)
```
NAME                                 READY   STATUS             RESTARTS      AGE
pod/fiware-orionld-548584cdf-6hc8b   0/1     Running            6 (3s ago)    3m38s
pod/fiware-orionld-548584cdf-q2dmk   0/1     CrashLoopBackOff   5 (18s ago)   3m38s
pod/fiware-orionld-548584cdf-r79sb   0/1     Running            6 (3s ago)    3m38s

NAME                             TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)          AGE
service/fiware-orionld-service   LoadBalancer   10.102.65.76   <pending>     1027:32497/TCP   3m38s

NAME                             READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/fiware-orionld   0/3     3            0           3m38s

NAME                                       DESIRED   CURRENT   READY   AGE
replicaset.apps/fiware-orionld-548584cdf   3         3         0       3m38s

NAME                                                     REFERENCE                   TARGETS                                     MINPODS   MAXPODS   REPLICAS   AGE
horizontalpodautoscaler.autoscaling/fiware-orionld-hpa   Deployment/fiware-orionld   cpu: <unknown>/30%, memory: <unknown>/70%   3         15        3          3m38s
```