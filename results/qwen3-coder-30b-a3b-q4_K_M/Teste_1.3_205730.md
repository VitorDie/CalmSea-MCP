# Relatório de Benchmark: 1-orion.yaml

* **Modelo:** `qwen3-coder:30b-a3b-q4_K_M`
* **Rodada:** 3
* **Status Final:** ❌ FALHA
* **HealthCheck:** Falha Crítica no Pod fiware-orionld-548584cdf-jjdqx: CrashLoopBackOff

## 🧠 Raciocínio do Agente
Executei: get_resource_details

## 📋 Estado Final do Namespace (teste-orion)
```
NAME                                 READY   STATUS             RESTARTS     AGE
pod/fiware-orionld-548584cdf-jjdqx   0/1     CrashLoopBackOff   4 (2s ago)   2m7s
pod/fiware-orionld-548584cdf-pm99g   0/1     CrashLoopBackOff   4 (2s ago)   2m7s
pod/fiware-orionld-548584cdf-q6l5t   0/1     CrashLoopBackOff   4 (2s ago)   2m7s

NAME                             TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)          AGE
service/fiware-orionld-service   LoadBalancer   10.110.37.92   <pending>     1027:30136/TCP   2m7s

NAME                             READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/fiware-orionld   0/3     3            0           2m7s

NAME                                       DESIRED   CURRENT   READY   AGE
replicaset.apps/fiware-orionld-548584cdf   3         3         0       2m7s

NAME                                                     REFERENCE                   TARGETS                              MINPODS   MAXPODS   REPLICAS   AGE
horizontalpodautoscaler.autoscaling/fiware-orionld-hpa   Deployment/fiware-orionld   cpu: <unknown>/30%, memory: 4%/70%   3         15        3          2m7s
```