# Relatório de Benchmark: 3-mysql.yaml

* **Modelo:** `qwen3.5:27b-q4_K_M`
* **Rodada:** 4
* **Status Final:** ❌ FALHA
* **HealthCheck:** Falha Crítica no Pod mysql-5b89c5cfc7-bdw5z: CrashLoopBackOff

## 🧠 Raciocínio do Agente
Executei: list_resources

## 📋 Estado Final do Namespace (teste-mysql)
```
NAME                         READY   STATUS             RESTARTS      AGE
pod/mysql-5b89c5cfc7-bdw5z   0/1     CrashLoopBackOff   2 (19s ago)   33s

NAME            TYPE        CLUSTER-IP    EXTERNAL-IP   PORT(S)    AGE
service/mysql   ClusterIP   10.107.8.95   <none>        3306/TCP   33s

NAME                    READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/mysql   0/1     1            0           33s

NAME                               DESIRED   CURRENT   READY   AGE
replicaset.apps/mysql-5b89c5cfc7   1         1         0       33s
```