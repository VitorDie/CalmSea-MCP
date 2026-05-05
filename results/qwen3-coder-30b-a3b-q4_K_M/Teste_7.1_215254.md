# Relatório de Benchmark: 7-elasticsearch.yaml

* **Modelo:** `qwen3-coder:30b-a3b-q4_K_M`
* **Rodada:** 1
* **Status Final:** ❌ FALHA
* **HealthCheck:** Timeout: Os recursos não atingiram estabilidade no tempo previsto

## 🧠 Raciocínio do Agente
Executei: get_resource_details
<parameter=name>
elasticsearch
</parameter>
<parameter=namespace>
teste-elasticsearch
</parameter>
<parameter=resource_type>
service
</parameter>
</function>
</tool_call>

## 📋 Estado Final do Namespace (teste-elasticsearch)
```
NAME                       DESIRED   CURRENT   READY   AGE
replicationcontroller/es   1         0         0       2m10s

NAME                    TYPE           CLUSTER-IP       EXTERNAL-IP   PORT(S)                         AGE
service/elasticsearch   LoadBalancer   10.109.187.234   <pending>     9200:31621/TCP,9300:32633/TCP   2m10s
```