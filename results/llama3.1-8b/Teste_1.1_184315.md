# Relatório: 1-orion.yaml - Rep 1

## Status Final: ❌ FALHA
**Veredito:** Falha: CrashLoopBackOff, CrashLoopBackOff, CrashLoopBackOff

---

## 🔍 Análise
{"name": "apply_manifest", "parameters": {"manifest": "{'apiVersion': 'v1', 'items': [{'apiVersion': 'apps/v1', 'kind': 'Deployment', 'metadata': {'annotations': {'deployment.kubernetes.io/revision': '2', 'kubectl.kubernetes.io/last-applied-configuration': '{"apiVersion":"apps/v1","kind":"Deployment","metadata":{"annotations":{},"name":"fiware-orionld","namespace":"teste-orion"},"spec":{"replicas":3,"selector":{"matchLabels":{"app":"orionld"}},"template":{"metadata":{"labels":{"app":"orionld"},"name":"fiware-orion"},"spec":{"containers":[{"args":["-dbhost","orionld-mongodb-svc:27017","-rplSet","orionld-mongodb","-dbuser","usuariozão","-dbpwd","123456789","-dbAuthMech","SCRAM-SHA-256","-db","orion","-statCounters","-statSemWait","-statTiming","-statNotifQueue"],"env":[{"name":"ORIONLD_MONGOCONLY","value":"TRUE"},{"name":"DB_PASSWORD","value":"hardcoded-password-123"},{"name":"API_KEY","value":"sk-1234567890abcdef"}],"image":"fiware/orion-ld","livenessProbe":{"httpGet":{"path":"/version","port":1026},"initialDelaySeconds":10,"periodSeconds":5},"name":"orion","ports":[{"containerPort":1026}],"readinessProbe":{"httpGet":{"path":"/version","port":1026},"initialDelaySeconds":5,"periodSeconds":5},"resources":{"limits":{"cpu":"500m","memory":"500Mi"},"requests":{"cpu":"100m","memory":"100Mi"}}}]}}"}}"}}", "namespace": "teste-orion"}}

Este comando aplica um manifesto Kubernetes YAML diretamente para o namespace "teste-orion" com as configurações de revisão 2.

## 🛠️ Fix Aplicado
```yaml
Código não extraído
```

## 📋 Cluster Snapshot
```
NAME                                 READY   STATUS             RESTARTS      AGE
pod/fiware-orionld-548584cdf-7jnbj   0/1     CrashLoopBackOff   6 (23s ago)   5m29s
pod/fiware-orionld-548584cdf-b4mzj   0/1     CrashLoopBackOff   6 (23s ago)   5m29s
pod/fiware-orionld-548584cdf-gg8bx   0/1     CrashLoopBackOff   6 (98s ago)   5m29s

NAME                             TYPE           CLUSTER-IP       EXTERNAL-IP   PORT(S)          AGE
service/fiware-orionld-service   LoadBalancer   10.110.204.221   <pending>     1027:30686/TCP   5m29s

NAME                             READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/fiware-orionld   0/3     3            0           5m29s

NAME                                       DESIRED   CURRENT   READY   AGE
replicaset.apps/fiware-orionld-548584cdf   3         3         0       5m29s

NAME                                                     REFERENCE                   TARGETS                                     MINPODS   MAXPODS   REPLICAS   AGE
horizontalpodautoscaler.autoscaling/fiware-orionld-hpa   Deployment/fiware-orionld   cpu: <unknown>/30%, memory: <unknown>/70%   3         15        3          5m29s
```