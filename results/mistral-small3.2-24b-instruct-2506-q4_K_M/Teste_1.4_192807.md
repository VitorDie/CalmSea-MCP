# Relatório de Benchmark: 1-orion.yaml

* **Modelo:** `mistral-small3.2:24b-instruct-2506-q4_K_M`
* **Rodada:** 4
* **Status Final:** ❌ FALHA
* **HealthCheck:** Falha Crítica no Pod fiware-orionld-548584cdf-2z4l7: CrashLoopBackOff

## 🧠 Raciocínio do Agente


## 📋 Estado Final do Namespace (teste-orion)
```
NAME                                 READY   STATUS             RESTARTS      AGE
pod/fiware-orionld-548584cdf-2z4l7   0/1     CrashLoopBackOff   4 (1s ago)    106s
pod/fiware-orionld-548584cdf-74x2m   0/1     Pending            0             106s
pod/fiware-orionld-548584cdf-8z7cr   0/1     Running            4 (16s ago)   106s

NAME                             TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)          AGE
service/fiware-orionld-service   LoadBalancer   10.109.101.44   <pending>     1027:31582/TCP   106s

NAME                             READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/fiware-orionld   0/3     3            0           106s

NAME                                       DESIRED   CURRENT   READY   AGE
replicaset.apps/fiware-orionld-548584cdf   3         3         0       106s

NAME                                                     REFERENCE                   TARGETS                              MINPODS   MAXPODS   REPLICAS   AGE
horizontalpodautoscaler.autoscaling/fiware-orionld-hpa   Deployment/fiware-orionld   cpu: <unknown>/30%, memory: 4%/70%   3         15        3          106s
```