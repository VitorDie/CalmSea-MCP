# Relatório de Benchmark: 1-orion.yaml

* **Modelo:** `o4-mini`
* **Rodada:** 1
* **Status Final:** ❌ FALHA
* **HealthCheck:** Falha Crítica no Pod fiware-orionld-5c556dd988-xf8fq: ErrImagePull

## 🧠 Raciocínio do Agente
Segue o diagnóstico geral, pontos de melhoria e os manifestos corrigidos para o Service, Deployment, Secret e HPA no namespace teste-orion.

1) Principais problemas encontrados  
- Selector do Service não bate com o label do Pod  
  • Service aponta para app=orionlds (plural)  
  • Deployment rotula pods com app=orionld (singular)  
  → o Service não está direcionando tráfego a nenhum Pod.  
- Credenciais e chaves expostas em clear‐text  
  • `DB_PASSWORD`, `API_KEY` e flags de conexão no args estão hardcoded  
  → não seguem boas práticas de segurança.  
- Falta de SecurityContext no Pod  
  • Container roda como root, sem isolamento de capacidades.  
  → expõe risco de breakout.  
- Imagem sem tag fixa  
  • `fiware/orion-ld` (latest) não garante reprodutibilidade.  
- HPA não revisado em detalhe  
  • sugerimos configurar alvo de CPU e min/max de réplicas.

2) Sugestões de correção  
- Unificar o label do Pod e o selector do Service (usar `app: fiware-orionld`).  
- Mover todas as variáveis sensíveis para um Secret K8s e referenciá-las via `envFrom`.  
- Adicionar `securityContext` de Pod e Container (runAsNonRoot, dropCapabilities, readOnlyRootFilesystem).  
- Fixar a tag da imagem (ex.: `fiware/orion-ld:2.8.0`).  
- Configurar HPA para target CPU 75%, com pelos menos 2–10 réplicas.

3) Manifestos corrigidos  

a) Secret (`fiware-orionld-secret.yaml`)  
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: fiware-orionld-secret
  namespace: teste-orion
type: Opaque
stringData:
  DB_HOST: orionld-mongodb-svc:27017
  DB_USER: usuariozao
  DB_PASSWORD: "123456789"
  API_KEY: sk-1234567890abcdef
```

b) Service (`fiware-orionld-service.yaml`)  
```yaml
apiVersion: v1
kind: Service
metadata:
  name: fiware-orionld-service
  namespace: teste-orion
  labels:
    app: fiware-orionld
spec:
  type: LoadBalancer
  selector:
    app: fiware-orionld
  ports:
    - port: 1027
      targetPort: 1026
      protocol: TCP
      name: http
  externalTrafficPolicy: Cluster
```

c) Deployment (`fiware-orionld-deployment.yaml`)  
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fiware-orionld
  namespace: teste-orion
  labels:
    app: fiware-orionld
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fiware-orionld
  template:
    metadata:
      labels:
        app: fiware-orionld
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 2000
      containers:
        - name: orion
          image: fiware/orion-ld:2.8.0
          imagePullPolicy: IfNotPresent
          args:
            - "-dbhost"
            - "$(DB_HOST)"
            - "-dbuser"
            - "$(DB_USER)"
            - "-dbpwd"
            - "$(DB_PASSWORD)"
            - "-dbAuthMech"
            - "SCRAM-SHA-256"
            - "-db"
            - "orion"
            - "-statCounters"
            - "-statSemWait"
            - "-statTiming"
            - "-statNotifQueue"
          envFrom:
            - secretRef:
                name: fiware-orionld-secret
          ports:
            - containerPort: 1026
              name: http
          resources:
            requests:
              cpu: 200m
              memory: 200Mi
            limits:
              cpu: 500m
              memory: 500Mi
          livenessProbe:
            httpGet:
              path: /version
              port: 1026
            initialDelaySeconds: 15
            periodSeconds: 10
            timeoutSeconds: 2
            failureThreshold: 5
          readinessProbe:
            httpGet:
              path: /version
              port: 1026
            initialDelaySeconds: 10
            periodSeconds: 5
            timeoutSeconds: 2
            failureThreshold: 3
          securityContext:
            allowPrivilegeEscalation: false
            capabilities:
              drop: ["ALL"]
            readOnlyRootFilesystem: true
      dnsPolicy: ClusterFirst
      restartPolicy: Always
```

d) HPA (`fiware-orionld-hpa.yaml`)  
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fiware-orionld-hpa
  namespace: teste-orion
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fiware-orionld
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 75
```

4) Próximos passos  
1. Fazer `kubectl apply --dry-run=client -f` em cada arquivo para validação.  
2. Aplicar no cluster com `kubectl apply -f`.  
3. Verificar rollout status e logs:  
   ```
   kubectl -n teste-orion rollout status deployment/fiware-orionld
   kubectl -n teste-orion logs svc/fiware-orionld-service
   ```
4. Ajustar HPA após coleta de métricas reais (via Metrics-Server ou Prometheus).

Com estas correções, garantimos consistência de labels, isolamento de credenciais, imagem versionada, segurança de execução e escalonamento automático em produção.

## 📋 Estado Final do Namespace (teste-orion)
```
NAME                                  READY   STATUS             RESTARTS   AGE
pod/fiware-orionld-5c556dd988-xf8fq   0/1     ErrImagePull       0          68s
pod/fiware-orionld-5cbcc6d659-v6lbz   0/1     ImagePullBackOff   0          50s
pod/fiware-orionld-668c7c6d97-tvktt   0/1     ErrImagePull       0          17s
pod/fiware-orionld-6bcddd5644-kljvn   0/1     Pending            0          32s

NAME                             TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)          AGE
service/fiware-orionld-service   LoadBalancer   10.111.237.52   <pending>     1027:32228/TCP   100s

NAME                             READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/fiware-orionld   0/3     1            0           100s

NAME                                        DESIRED   CURRENT   READY   AGE
replicaset.apps/fiware-orionld-548584cdf    0         0         0       100s
replicaset.apps/fiware-orionld-5c556dd988   1         1         0       68s
replicaset.apps/fiware-orionld-5cbcc6d659   1         1         0       50s
replicaset.apps/fiware-orionld-668c7c6d97   1         1         0       17s
replicaset.apps/fiware-orionld-6bcddd5644   1         1         0       32s

NAME                                                     REFERENCE                   TARGETS              MINPODS   MAXPODS   REPLICAS   AGE
horizontalpodautoscaler.autoscaling/fiware-orionld-hpa   Deployment/fiware-orionld   cpu: <unknown>/50%   3         10        3          100s
```