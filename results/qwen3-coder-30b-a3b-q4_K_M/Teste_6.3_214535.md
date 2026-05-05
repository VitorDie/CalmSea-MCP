# Relatório de Benchmark: 6-selenium.yaml

* **Modelo:** `qwen3-coder:30b-a3b-q4_K_M`
* **Rodada:** 3
* **Status Final:** ❌ FALHA
* **HealthCheck:** Timeout: Os recursos não atingiram estabilidade no tempo previsto

## 🧠 Raciocínio do Agente
Executei: get_resource_details

## 📋 Estado Final do Namespace (teste-selenium)
```
NAME                                READY   STATUS    RESTARTS   AGE
pod/selenium-hub-5469ddb6dd-cbgnk   0/1     Pending   0          2m11s

NAME                   TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)                                        AGE
service/selenium-hub   NodePort   10.103.103.97   <none>        4444:31069/TCP,4443:30225/TCP,4442:31194/TCP   2m11s

NAME                           READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/selenium-hub   0/1     1            0           2m11s

NAME                                      DESIRED   CURRENT   READY   AGE
replicaset.apps/selenium-hub-5469ddb6dd   1         1         0       2m11s
```