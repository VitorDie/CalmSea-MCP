# Relatório: 2-frontend.yaml - Rep 1

## Status Final: ❌ FALHA
**Veredito:** Falha: ImagePullBackOff

---

## 🔍 Análise
✅ **Executado apply_manifest:**

```json
🚀 **Aplicado:** {'status': 'error', 'message': 'Erro do K8s: error: error parsing STDIN: error converting YAML to JSON: yaml: line 42: mapping values are not allowed in this context\n'}
```

## 🛠️ Fix Aplicado
```yaml
Código não extraído
```

## 📋 Cluster Snapshot
```
NAME                            READY   STATUS             RESTARTS   AGE
pod/frontend-65d44dd469-s222c   0/1     ImagePullBackOff   0          4m52s

NAME                       READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/frontend   0/1     1            0           4m52s

NAME                                  DESIRED   CURRENT   READY   AGE
replicaset.apps/frontend-65d44dd469   1         1         0       4m52s
```