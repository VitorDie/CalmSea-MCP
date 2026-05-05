# Relatório de Benchmark: 3-mysql.yaml

* **Modelo:** `qwen3.5:27b-q4_K_M`
* **Rodada:** 5
* **Status Final:** ❌ FALHA
* **HealthCheck:** Timeout: Os recursos não atingiram estabilidade no tempo previsto

## 🧠 Raciocínio do Agente
Executei: list_resources

## 📋 Estado Final do Namespace (teste-mysql)
```
NAME        READY   STATUS    RESTARTS   AGE
pod/mysql   0/1     Pending   0          5m48s

NAME            TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)    AGE
service/mysql   ClusterIP   None         <none>        3306/TCP   2m35s

NAME                     READY   AGE
statefulset.apps/mysql   0/1     2m35s
```