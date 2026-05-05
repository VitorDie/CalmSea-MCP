# Relatório de Benchmark: 3-mysql.yaml

* **Modelo:** `qwen3.5:27b-q4_K_M`
* **Rodada:** 2
* **Status Final:** ❌ FALHA
* **HealthCheck:** Timeout: Os recursos não atingiram estabilidade no tempo previsto

## 🧠 Raciocínio do Agente
Executei: list_resources

## 📋 Estado Final do Namespace (teste-mysql)
```
NAME                         READY   STATUS    RESTARTS   AGE
pod/mysql                    0/1     Pending   0          8m43s
pod/mysql-677fd5f4c4-pbfk2   0/1     Pending   0          2m12s

NAME            TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE
service/mysql   ClusterIP   10.105.64.104   <none>        3306/TCP   5m23s

NAME                    READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/mysql   0/1     1            0           5m23s

NAME                               DESIRED   CURRENT   READY   AGE
replicaset.apps/mysql-677fd5f4c4   1         1         0       2m12s
replicaset.apps/mysql-867cb6df45   0         0         0       5m23s
```