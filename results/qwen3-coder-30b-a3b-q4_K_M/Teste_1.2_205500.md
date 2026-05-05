# Relatório de Benchmark: 1-orion.yaml

* **Modelo:** `qwen3-coder:30b-a3b-q4_K_M`
* **Rodada:** 2
* **Status Final:** ❌ FALHA
* **HealthCheck:** Falha Crítica no Pod fiware-orionld-548584cdf-j5xvn: CrashLoopBackOff

## 🧠 Raciocínio do Agente
Executei: get_resource_details

## 📋 Estado Final do Namespace (teste-orion)
```
NAME                                 READY   STATUS             RESTARTS      AGE
pod/fiware-orionld-548584cdf-47xwl   0/1     Running            4 (16s ago)   102s
pod/fiware-orionld-548584cdf-j5xvn   0/1     CrashLoopBackOff   4 (1s ago)    102s
pod/fiware-orionld-548584cdf-zflvx   0/1     Running            4 (16s ago)   102s

NAME                             TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)          AGE
service/fiware-orionld-service   LoadBalancer   10.105.70.172   <pending>     1027:30343/TCP   102s

NAME                             READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/fiware-orionld   0/3     3            0           102s

NAME                                       DESIRED   CURRENT   READY   AGE
replicaset.apps/fiware-orionld-548584cdf   3         3         0       102s

NAME                                                     REFERENCE                   TARGETS                              MINPODS   MAXPODS   REPLICAS   AGE
horizontalpodautoscaler.autoscaling/fiware-orionld-hpa   Deployment/fiware-orionld   cpu: <unknown>/30%, memory: 4%/70%   3         15        3          101s
```