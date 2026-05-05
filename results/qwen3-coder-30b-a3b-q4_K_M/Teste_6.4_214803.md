# Relatório de Benchmark: 6-selenium.yaml

* **Modelo:** `qwen3-coder:30b-a3b-q4_K_M`
* **Rodada:** 4
* **Status Final:** ❌ FALHA
* **HealthCheck:** Timeout: Os recursos não atingiram estabilidade no tempo previsto

## 🧠 Raciocínio do Agente
Executei: get_resource_details

## 📋 Estado Final do Namespace (teste-selenium)
```
NAME                                READY   STATUS    RESTARTS   AGE
pod/selenium-hub-5469ddb6dd-swzct   0/1     Pending   0          2m11s

NAME                   TYPE       CLUSTER-IP       EXTERNAL-IP   PORT(S)                                        AGE
service/selenium-hub   NodePort   10.108.193.107   <none>        4444:31039/TCP,4443:30764/TCP,4442:32117/TCP   2m11s

NAME                           READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/selenium-hub   0/1     1            0           2m11s

NAME                                      DESIRED   CURRENT   READY   AGE
replicaset.apps/selenium-hub-5469ddb6dd   1         1         0       2m11s
```