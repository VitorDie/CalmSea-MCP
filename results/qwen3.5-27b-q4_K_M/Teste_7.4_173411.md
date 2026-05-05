# Relatório de Benchmark: 7-elasticsearch.yaml

* **Modelo:** `qwen3.5:27b-q4_K_M`
* **Rodada:** 4
* **Status Final:** ❌ FALHA
* **HealthCheck:** Timeout: Os recursos não atingiram estabilidade no tempo previsto

## 🧠 Raciocínio do Agente
Executei: apply_manifest

## 📋 Estado Final do Namespace (teste-elasticsearch)
```
NAME                       DESIRED   CURRENT   READY   AGE
replicationcontroller/es   1         0         0       10m

NAME                    TYPE        CLUSTER-IP    EXTERNAL-IP   PORT(S)             AGE
service/elasticsearch   ClusterIP   10.100.5.11   <none>        9200/TCP,9300/TCP   10m
```