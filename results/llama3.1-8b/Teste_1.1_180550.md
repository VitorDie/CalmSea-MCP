# Relatório: 1-orion.yaml - Rep 1

## Status Final: ❌ FALHA
**Veredito:** Falha: CrashLoopBackOff, CrashLoopBackOff, CrashLoopBackOff

---

## 🔍 Análise
✅ **Executado apply_manifest:**

```json
❌ Erro na execução: 'namespace'
```

## 🛠️ Fix Aplicado
```yaml
Código não extraído
```

## 📋 Cluster Snapshot
```
NAME                                 READY   STATUS             RESTARTS     AGE
pod/fiware-orionld-548584cdf-gmpcq   0/1     CrashLoopBackOff   5 (5s ago)   3m21s
pod/fiware-orionld-548584cdf-k4rzj   0/1     CrashLoopBackOff   5 (5s ago)   3m21s
pod/fiware-orionld-548584cdf-r7vrg   0/1     CrashLoopBackOff   5 (5s ago)   3m21s

NAME                             TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)          AGE
service/fiware-orionld-service   LoadBalancer   10.96.56.169   <pending>     1027:31659/TCP   3m21s

NAME                             READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/fiware-orionld   0/3     3            0           3m21s

NAME                                       DESIRED   CURRENT   READY   AGE
replicaset.apps/fiware-orionld-548584cdf   3         3         0       3m21s

NAME                                                     REFERENCE                   TARGETS                                     MINPODS   MAXPODS   REPLICAS   AGE
horizontalpodautoscaler.autoscaling/fiware-orionld-hpa   Deployment/fiware-orionld   cpu: <unknown>/30%, memory: <unknown>/70%   3         15        3          3m21s
```