# Relatório de Benchmark: 1-orion.yaml

* **Modelo:** `mistral-small3.2:24b-instruct-2506-q4_K_M`
* **Rodada:** 5
* **Status Final:** ❌ FALHA
* **HealthCheck:** Falha Crítica no Pod fiware-orionld-548584cdf-p8lbj: CrashLoopBackOff

## 🧠 Raciocínio do Agente


## 📋 Estado Final do Namespace (teste-orion)
```
NAME                                 READY   STATUS             RESTARTS      AGE
pod/fiware-orionld-548584cdf-dwkrm   0/1     Pending            0             111s
pod/fiware-orionld-548584cdf-p8lbj   0/1     CrashLoopBackOff   4 (6s ago)    111s
pod/fiware-orionld-548584cdf-qcn6j   0/1     Running            4 (21s ago)   111s

NAME                             TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)          AGE
service/fiware-orionld-service   LoadBalancer   10.109.156.1   <pending>     1027:30809/TCP   111s

NAME                             READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/fiware-orionld   0/3     3            0           111s

NAME                                       DESIRED   CURRENT   READY   AGE
replicaset.apps/fiware-orionld-548584cdf   3         3         0       111s

NAME                                                     REFERENCE                   TARGETS                                     MINPODS   MAXPODS   REPLICAS   AGE
horizontalpodautoscaler.autoscaling/fiware-orionld-hpa   Deployment/fiware-orionld   cpu: <unknown>/30%, memory: <unknown>/70%   3         15        3          111s
```