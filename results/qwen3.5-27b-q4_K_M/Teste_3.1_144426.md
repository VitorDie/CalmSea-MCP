# Relatório de Benchmark: 3-mysql.yaml

* **Modelo:** `qwen3.5:27b-q4_K_M`
* **Rodada:** 1
* **Status Final:** ❌ FALHA
* **HealthCheck:** Falha Crítica no Pod mysql-756768b77f-bkd5f: CrashLoopBackOff

## 🧠 Raciocínio do Agente
Executei: list_resources

## 📋 Estado Final do Namespace (teste-mysql)
```
NAME                         READY   STATUS             RESTARTS     AGE
pod/mysql-756768b77f-bkd5f   0/1     CrashLoopBackOff   2 (3s ago)   41s

NAME            TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)    AGE
service/mysql   ClusterIP   10.107.5.233   <none>        3306/TCP   41s

NAME                    READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/mysql   0/1     1            0           42s

NAME                               DESIRED   CURRENT   READY   AGE
replicaset.apps/mysql-756768b77f   1         1         0       42s
```