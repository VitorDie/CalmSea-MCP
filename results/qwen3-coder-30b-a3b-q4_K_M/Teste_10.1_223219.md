# Relatório de Benchmark: 10-mongodb.yaml

* **Modelo:** `qwen3-coder:30b-a3b-q4_K_M`
* **Rodada:** 1
* **Status Final:** ✅ SUCESSO
* **HealthCheck:** Sucesso: Ambiente íntegro e estável

## 🧠 Raciocínio do Agente
Executei: delete_resource

## 📋 Estado Final do Namespace (teste-mongodb)
```
NAME                                      READY   STATUS        RESTARTS   AGE
pod/mongodb-deployment-559d9986d4-f4gmv   1/1     Terminating   0          21s

NAME                      TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)     AGE
service/mongodb-service   ClusterIP   10.97.169.220   <none>        27017/TCP   21s
```