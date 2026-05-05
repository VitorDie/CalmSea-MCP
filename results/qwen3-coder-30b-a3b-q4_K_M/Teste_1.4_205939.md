# Relatório de Benchmark: 1-orion.yaml

* **Modelo:** `qwen3-coder:30b-a3b-q4_K_M`
* **Rodada:** 4
* **Status Final:** ❌ FALHA
* **HealthCheck:** Falha Crítica no Pod fiware-orionld-548584cdf-9w25l: CrashLoopBackOff

## 🧠 Raciocínio do Agente
Executei: get_resource_details

## 📋 Estado Final do Namespace (teste-orion)
```
NAME                                 READY   STATUS             RESTARTS      AGE
pod/fiware-orionld-548584cdf-9w25l   0/1     CrashLoopBackOff   4 (1s ago)    106s
pod/fiware-orionld-548584cdf-l5hq7   0/1     Running            4 (6s ago)    106s
pod/fiware-orionld-548584cdf-zdtjm   0/1     Running            4 (11s ago)   106s

NAME                             TYPE           CLUSTER-IP       EXTERNAL-IP   PORT(S)          AGE
service/fiware-orionld-service   LoadBalancer   10.106.187.193   <pending>     1027:31593/TCP   106s

NAME                             READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/fiware-orionld   0/3     3            0           106s

NAME                                       DESIRED   CURRENT   READY   AGE
replicaset.apps/fiware-orionld-548584cdf   3         3         0       106s

NAME                                                     REFERENCE                   TARGETS                              MINPODS   MAXPODS   REPLICAS   AGE
horizontalpodautoscaler.autoscaling/fiware-orionld-hpa   Deployment/fiware-orionld   cpu: <unknown>/30%, memory: 4%/70%   3         15        3          106s
```