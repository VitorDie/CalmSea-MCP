# Relatório de Benchmark: 7-elasticsearch.yaml

* **Modelo:** `qwen3.5:27b-q4_K_M`
* **Rodada:** 1
* **Status Final:** ❌ FALHA
* **HealthCheck:** Timeout: Os recursos não atingiram estabilidade no tempo previsto

## 🧠 Raciocínio do Agente
Executei: list_resources

## 📋 Estado Final do Namespace (teste-elasticsearch)
```
NAME                       DESIRED   CURRENT   READY   AGE
replicationcontroller/es   1         0         0       3m31s

NAME                    TYPE           CLUSTER-IP       EXTERNAL-IP   PORT(S)                         AGE
service/elasticsearch   LoadBalancer   10.102.117.215   <pending>     9200:30446/TCP,9300:31968/TCP   3m31s
```