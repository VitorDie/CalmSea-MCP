# Relatório de Benchmark: 10-mongodb.yaml

* **Modelo:** `qwen3-coder:30b-a3b-q4_K_M`
* **Rodada:** 4
* **Status Final:** ✅ SUCESSO
* **HealthCheck:** Sucesso: Ambiente íntegro e estável

## 🧠 Raciocínio do Agente
Executei: apply_manifest

## 📋 Estado Final do Namespace (teste-mongodb)
```
NAME                                      READY   STATUS    RESTARTS   AGE
pod/mongodb-deployment-559d9986d4-plnl5   1/1     Running   0          22s

NAME                      TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)     AGE
service/mongodb-service   ClusterIP   10.104.163.127   <none>        27017/TCP   22s

NAME                                 READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/mongodb-deployment   1/1     1            1           22s

NAME                                            DESIRED   CURRENT   READY   AGE
replicaset.apps/mongodb-deployment-559d9986d4   1         1         1       22s
```