# Relatório de Benchmark: 1-orion.yaml

* **Modelo:** `qwen3-coder:30b-a3b-q4_K_M`
* **Rodada:** 5
* **Status Final:** ❌ FALHA
* **HealthCheck:** Falha Crítica no Pod fiware-orionld-548584cdf-57wrr: CrashLoopBackOff

## 🧠 Raciocínio do Agente
Executei: get_resource_details

## 📋 Estado Final do Namespace (teste-orion)
```
NAME                                 READY   STATUS             RESTARTS      AGE
pod/fiware-orionld-548584cdf-57wrr   0/1     CrashLoopBackOff   4 (1s ago)    107s
pod/fiware-orionld-548584cdf-p7qx6   0/1     Running            4 (16s ago)   107s
pod/fiware-orionld-548584cdf-rdlvv   0/1     CrashLoopBackOff   4 (1s ago)    107s

NAME                             TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)          AGE
service/fiware-orionld-service   LoadBalancer   10.98.227.37   <pending>     1027:30499/TCP   107s

NAME                             READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/fiware-orionld   0/3     3            0           107s

NAME                                       DESIRED   CURRENT   READY   AGE
replicaset.apps/fiware-orionld-548584cdf   3         3         0       107s

NAME                                                     REFERENCE                   TARGETS                              MINPODS   MAXPODS   REPLICAS   AGE
horizontalpodautoscaler.autoscaling/fiware-orionld-hpa   Deployment/fiware-orionld   cpu: <unknown>/30%, memory: 4%/70%   3         15        3          107s
```