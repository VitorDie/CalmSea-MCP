# Relatório de Benchmark: 6-selenium.yaml

* **Modelo:** `mistral-small3.2:24b-instruct-2506-q4_K_M`
* **Rodada:** 5
* **Status Final:** ❌ FALHA
* **HealthCheck:** Timeout: Os recursos não atingiram estabilidade no tempo previsto

## 🧠 Raciocínio do Agente


## 📋 Estado Final do Namespace (teste-selenium)
```
NAME                                READY   STATUS    RESTARTS   AGE
pod/selenium-hub-5469ddb6dd-6sqtg   0/1     Pending   0          2m13s

NAME                   TYPE       CLUSTER-IP     EXTERNAL-IP   PORT(S)                                        AGE
service/selenium-hub   NodePort   10.98.77.216   <none>        4444:30569/TCP,4443:31157/TCP,4442:30148/TCP   2m14s

NAME                           READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/selenium-hub   0/1     1            0           2m14s

NAME                                      DESIRED   CURRENT   READY   AGE
replicaset.apps/selenium-hub-5469ddb6dd   1         1         0       2m14s
```