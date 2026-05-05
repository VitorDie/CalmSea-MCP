# Relatório de Benchmark: 1-orion.yaml

* **Modelo:** `mistral-small3.2:24b-instruct-2506-q4_K_M`
* **Rodada:** 3
* **Status Final:** ❌ FALHA
* **HealthCheck:** Falha Crítica no Pod fiware-orionld-548584cdf-5gcrs: CrashLoopBackOff

## 🧠 Raciocínio do Agente


## 📋 Estado Final do Namespace (teste-orion)
```
NAME                                 READY   STATUS             RESTARTS      AGE
pod/fiware-orionld-548584cdf-5gcrs   0/1     CrashLoopBackOff   4 (41s ago)   2m31s
pod/fiware-orionld-548584cdf-9l4s6   0/1     Pending            0             2m31s
pod/fiware-orionld-548584cdf-jhxb9   0/1     CrashLoopBackOff   4 (46s ago)   2m31s

NAME                             TYPE           CLUSTER-IP       EXTERNAL-IP   PORT(S)          AGE
service/fiware-orionld-service   LoadBalancer   10.110.213.193   <pending>     1027:30987/TCP   2m31s

NAME                             READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/fiware-orionld   0/3     3            0           2m31s

NAME                                       DESIRED   CURRENT   READY   AGE
replicaset.apps/fiware-orionld-548584cdf   3         3         0       2m31s

NAME                                                     REFERENCE                   TARGETS                                     MINPODS   MAXPODS   REPLICAS   AGE
horizontalpodautoscaler.autoscaling/fiware-orionld-hpa   Deployment/fiware-orionld   cpu: <unknown>/30%, memory: <unknown>/70%   3         15        3          2m31s
```