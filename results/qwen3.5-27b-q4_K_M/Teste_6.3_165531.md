# Relatório de Benchmark: 6-selenium.yaml

* **Modelo:** `qwen3.5:27b-q4_K_M`
* **Rodada:** 3
* **Status Final:** ❌ FALHA
* **HealthCheck:** Falha Crítica no Pod selenium-hub-6659c55f94-89s7r: CrashLoopBackOff

## 🧠 Raciocínio do Agente
Executei: list_resources

## 📋 Estado Final do Namespace (teste-selenium)
```
NAME                                READY   STATUS             RESTARTS     AGE
pod/selenium-hub-6659c55f94-89s7r   0/1     CrashLoopBackOff   1 (5s ago)   23s
pod/selenium-hub-6659c55f94-h9lkr   0/1     Pending            0            23s

NAME                   TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)                                AGE
service/selenium-hub   ClusterIP   10.108.3.222   <none>        4444/TCP,4443/TCP,4442/TCP,65000/TCP   23s

NAME                           READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/selenium-hub   0/2     2            0           24s

NAME                                      DESIRED   CURRENT   READY   AGE
replicaset.apps/selenium-hub-6659c55f94   2         2         0       23s
```