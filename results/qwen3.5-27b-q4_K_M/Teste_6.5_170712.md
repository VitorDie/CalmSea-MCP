# Relatório de Benchmark: 6-selenium.yaml

* **Modelo:** `qwen3.5:27b-q4_K_M`
* **Rodada:** 5
* **Status Final:** ❌ FALHA
* **HealthCheck:** Falha Crítica no Pod selenium-hub-789b8c995d-mwcm8: CrashLoopBackOff

## 🧠 Raciocínio do Agente
Executei: list_resources

## 📋 Estado Final do Namespace (teste-selenium)
```
NAME                                READY   STATUS             RESTARTS     AGE
pod/selenium-hub-789b8c995d-26zmb   0/1     Pending            0            9s
pod/selenium-hub-789b8c995d-mwcm8   0/1     CrashLoopBackOff   1 (6s ago)   9s

NAME                   TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)                                AGE
service/selenium-hub   ClusterIP   10.100.239.140   <none>        4444/TCP,4443/TCP,4442/TCP,65000/TCP   9s

NAME                           READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/selenium-hub   0/2     2            0           9s

NAME                                      DESIRED   CURRENT   READY   AGE
replicaset.apps/selenium-hub-789b8c995d   2         2         0       9s
```