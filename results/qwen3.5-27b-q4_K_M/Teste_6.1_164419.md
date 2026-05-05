# Relatório de Benchmark: 6-selenium.yaml

* **Modelo:** `qwen3.5:27b-q4_K_M`
* **Rodada:** 1
* **Status Final:** ❌ FALHA
* **HealthCheck:** Timeout: Os recursos não atingiram estabilidade no tempo previsto

## 🧠 Raciocínio do Agente
Executei: list_resources

## 📋 Estado Final do Namespace (teste-selenium)
```
NAME                   TYPE        CLUSTER-IP    EXTERNAL-IP   PORT(S)                                AGE
service/selenium-hub   ClusterIP   10.98.16.74   <none>        4444/TCP,4443/TCP,4442/TCP,65000/TCP   2m10s

NAME                           READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/selenium-hub   0/2     0            0           2m10s

NAME                                      DESIRED   CURRENT   READY   AGE
replicaset.apps/selenium-hub-6c5f848457   2         0         0       2m10s
```