# Relatório de Benchmark: 7-elasticsearch.yaml

* **Modelo:** `qwen3.5:27b-q4_K_M`
* **Rodada:** 3
* **Status Final:** ❌ FALHA
* **HealthCheck:** Timeout: Os recursos não atingiram estabilidade no tempo previsto

## 🧠 Raciocínio do Agente
Executei: list_resources

## 📋 Estado Final do Namespace (teste-elasticsearch)
```
NAME                       DESIRED   CURRENT   READY   AGE
replicationcontroller/es   1         0         0       3m47s

NAME                    TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)                         AGE
service/elasticsearch   LoadBalancer   10.102.157.48   <pending>     9200:31825/TCP,9300:30964/TCP   3m48s
```