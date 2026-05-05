# Relatório de Benchmark: 8-newrelic.yaml

* **Modelo:** `qwen3.5:27b-q4_K_M`
* **Rodada:** 3
* **Status Final:** ❌ FALHA
* **HealthCheck:** Timeout: Os recursos não atingiram estabilidade no tempo previsto

## 🧠 Raciocínio do Agente
Executei: apply_manifest

## 📋 Estado Final do Namespace (teste-newrelic)
```
NAME                       READY   STATUS              RESTARTS   AGE
pod/newrelic-agent-z55xw   0/1     ContainerCreating   0          3m52s

NAME                            DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE   NODE SELECTOR   AGE
daemonset.apps/newrelic-agent   1         1         0       1            0           <none>          3m52s
```