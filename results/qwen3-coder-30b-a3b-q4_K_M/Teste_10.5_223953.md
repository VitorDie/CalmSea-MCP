# Relatório de Benchmark: 10-mongodb.yaml

* **Modelo:** `qwen3-coder:30b-a3b-q4_K_M`
* **Rodada:** 5
* **Status Final:** ❌ FALHA
* **HealthCheck:** Timeout: Os recursos não atingiram estabilidade no tempo previsto

## 🧠 Raciocínio do Agente
Executei: apply_manifest

## 📋 Estado Final do Namespace (teste-mongodb)
```
NAME                                      READY   STATUS    RESTARTS   AGE
pod/mongodb-deployment-559d9986d4-n7nbx   1/1     Running   0          2m26s
pod/mongodb-deployment-6ffff978b5-vdvws   0/1     Pending   0          2m3s

NAME                      TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)     AGE
service/mongodb-service   ClusterIP   10.110.6.185   <none>        27017/TCP   2m26s

NAME                                 READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/mongodb-deployment   1/1     1            1           2m26s

NAME                                            DESIRED   CURRENT   READY   AGE
replicaset.apps/mongodb-deployment-559d9986d4   1         1         1       2m26s
replicaset.apps/mongodb-deployment-6ffff978b5   1         1         0       2m3s
```