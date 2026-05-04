# Relatório de Benchmark: 8-newrelic.yaml

* **Modelo:** `o4-mini`
* **Rodada:** 2
* **Status Final:** ❌ FALHA
* **HealthCheck:** Falha Crítica no Pod newrelic-agent-sgdbs: CrashLoopBackOff

## 🧠 Raciocínio do Agente
A seguir um resumo dos principais pontos encontrados e uma proposta de manifesto atualizado com boas práticas. Note que, hoje, no namespace `teste-newrelic` só existe mesmo o DaemonSet (e os recursos de suporte: ServiceAccount e Secret). Não há Service nem Deployment para o agente New Relic — caso você precise expor alguma porta ou rodar o agente em modelo Deployment em vez de DaemonSet, por favor sinalize para criarmos.

1) Problemas / melhorias identificadas  
   - Não há `resources.requests`/`limits`  
   - Ausência de probes (readiness/liveness)  
   - Imagem sem tag fixa nem digest  
   - Ausência de `securityContext` (rodar como não-root)  
   - Sem `nodeSelector`/`tolerations` para casos de master taints  
   - Labels/annotations básicas faltando  
   - Sem `priorityClassName` nem TopologySpreadConstraints (para alta disponibilidade)  

2) Manifesto proposto  
```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: newrelic-agent
  namespace: teste-newrelic
  labels:
    app: newrelic-agent
spec:
  selector:
    matchLabels:
      app: newrelic-agent
  template:
    metadata:
      labels:
        app: newrelic-agent
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port:   "9103"
    spec:
      serviceAccountName: newrelic-agent-sa
      # permite scheduling em masters se desejado
      tolerations:
      - key: node-role.kubernetes.io/master
        operator: Exists
        effect: NoSchedule
      nodeSelector:
        kubernetes.io/os: linux
      securityContext:
        runAsNonRoot: true
        runAsUser: 1001
      priorityClassName: system-node-critical
      volumes:
      - name: docker-sock
        hostPath:
          path: /var/run/docker.sock
      - name: rootfs
        hostPath:
          path: /
      - name: sys
        hostPath:
          path: /sys
      - name: proc
        hostPath:
          path: /proc
      containers:
      - name: newrelic-agent
        # pin para versão específica
        image: newrelic/infrastructure:1.34.1@sha256:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        imagePullPolicy: IfNotPresent
        resources:
          requests:
            cpu:    50m
            memory: 128Mi
          limits:
            cpu:    200m
            memory: 256Mi
        env:
        - name: NR_LICENSE_KEY
          valueFrom:
            secretKeyRef:
              name: newrelic-license
              key: license
        volumeMounts:
        - name: docker-sock
          mountPath: /var/run/docker.sock
        - name: rootfs
          mountPath: /host/rootfs
          readOnly: true
        - name: sys
          mountPath: /host/sys
          readOnly: true
        - name: proc
          mountPath: /host/proc
          readOnly: true
        readinessProbe:
          exec:
            command: ["/usr/bin/newrelic-infra", "status"]
          initialDelaySeconds: 10
          periodSeconds: 30
        livenessProbe:
          exec:
            command: ["/usr/bin/newrelic-infra", "status"]
          initialDelaySeconds: 60
          periodSeconds: 60
```  

3) Próximos passos  
- Se quiser expor métricas (via Service) ou criar um Deployment em vez de DaemonSet, confirme o escopo e portas.  
- Para aplicar, basta usar:  
  `kubectl apply -f newrelic-daemonset.yaml --namespace=teste-newrelic`  
- Garanta também que exista uma Role/ClusterRole e Binding para `newrelic-agent-sa` com permissões necessárias ao agente.  

Fico à disposição para ajustar ou gerar o Service/Deployment conforme sua necessidade.

## 📋 Estado Final do Namespace (teste-newrelic)
```
NAME                       READY   STATUS             RESTARTS     AGE
pod/newrelic-agent-sgdbs   0/1     CrashLoopBackOff   1 (6s ago)   29s

NAME                            DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE   NODE SELECTOR            AGE
daemonset.apps/newrelic-agent   1         1         0       1            0           kubernetes.io/os=linux   29s
```