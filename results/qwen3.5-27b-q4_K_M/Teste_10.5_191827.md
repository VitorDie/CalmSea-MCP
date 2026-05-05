# Relatório de Benchmark: 10-mongodb.yaml

* **Modelo:** `qwen3.5:27b-q4_K_M`
* **Rodada:** 5
* **Status Final:** ❌ FALHA
* **HealthCheck:** Timeout: Os recursos não atingiram estabilidade no tempo previsto

## 🧠 Raciocínio do Agente
Executei: list_resources

## 📋 Estado Final do Namespace (teste-mongodb)
```
NAME                                      READY   STATUS    RESTARTS   AGE
pod/mongodb-deployment-745f6dd69c-d8sd8   0/1     Pending   0          2m9s
pod/mongodb-deployment-745f6dd69c-j4rpl   0/1     Pending   0          2m9s

NAME                      TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)     AGE
service/mongodb-service   ClusterIP   10.107.83.233   <none>        27017/TCP   2m10s

NAME                                 READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/mongodb-deployment   0/2     2            0           2m10s

NAME                                            DESIRED   CURRENT   READY   AGE
replicaset.apps/mongodb-deployment-745f6dd69c   2         2         0       2m10s
```