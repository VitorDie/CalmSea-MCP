# Relatório de Benchmark: 1-orion.yaml

* **Modelo:** `o4-mini`
* **Rodada:** 3
* **Status Final:** ❌ FALHA
* **HealthCheck:** Falha Crítica no Pod fiware-orionld-5f9f8dc9ff-4n977: ErrImagePull

## 🧠 Raciocínio do Agente
A seguir um levantamento dos principais pontos de “drift” e más-configurações que identifiquei, junto às recomendações e o manifesto pronto para deletar/recriar os recursos de forma coerente com boas práticas:

1) Service fiware-orionld-service  
   - Selector errado: o Service aponta para `app: orionlds` enquanto o Deployment usa `app: orionld`.  
   - Porta de serviço e targetPort embaralhados (1027 → 1026); falta nomear a porta.  
   - Falta labels “standard” (app.kubernetes.io/…) para rastreabilidade.  

2) Deployment fiware-orionld  
   - Não especifica tag de imagem (usa `fiware/orion-ld:latest` implicitamente). → travar em `:3.1.0` ou digest.  
   - Credenciais hard-coded (`DB_PASSWORD`, `API_KEY` e `-dbpwd 123456789`) expostas em args e env.  
   - Falta Secret para os dados sensíveis e uso de `valueFrom`.  
   - Falta podSecurityContext e securityContext no container (runAsNonRoot, drop all, read-only FS).  
   - Falta labels de versão e consistência com selector imutável.  

3) HPA fiware-orionld-hpa  
   - Está correto, só sugiro ajustar target CPU para 50% (mais usual em produção).

---

Para aplicar as correções, o mais simples é:

  a) remover o Deployment existente (pois o selector é imutável)  
  b) aplicar, na ordem, Secret → Service → Deployment → HPA  

Segue o YAML final:

```yaml
# 1) Secret para DB_PASSWORD e API_KEY
apiVersion: v1
kind: Secret
metadata:
  name: fiware-orionld-secret
  namespace: teste-orion
type: Opaque
stringData:
  db-password: 123456789       # ou seu valor real
  api-key: sk-1234567890abcdef # ou seu valor real

---
# 2) Service corrigido
apiVersion: v1
kind: Service
metadata:
  name: fiware-orionld-service
  namespace: teste-orion
  labels:
    app.kubernetes.io/name: orion-ld
    app.kubernetes.io/instance: fiware-orionld
spec:
  type: LoadBalancer
  selector:
    app.kubernetes.io/instance: fiware-orionld
  ports:
    - name: http
      port: 1026
      targetPort: 1026
      protocol: TCP

---
# 3) Deployment recriado
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fiware-orionld
  namespace: teste-orion
  labels:
    app.kubernetes.io/name: orion-ld
    app.kubernetes.io/instance: fiware-orionld
    app.kubernetes.io/version: "3.1.0"
spec:
  replicas: 3
  selector:
    matchLabels:
      app.kubernetes.io/instance: fiware-orionld
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%
      maxUnavailable: 25%
  template:
    metadata:
      labels:
        app.kubernetes.io/name: orion-ld
        app.kubernetes.io/instance: fiware-orionld
        app.kubernetes.io/version: "3.1.0"
    spec:
      podSecurityContext:
        runAsNonRoot: true
        runAsUser: 1000
      containers:
        - name: orion
          image: fiware/orion-ld:3.1.0
          imagePullPolicy: IfNotPresent
          args:
            - -dbhost
            - orionld-mongodb-svc:27017
            - -rplSet
            - orionld-mongodb
            - -dbuser
            - usuariozão
            - -dbpwd
            - "$(DB_PASSWORD)"
            - -dbAuthMech
            - SCRAM-SHA-256
            - -db
            - orion
            - -statCounters
            - -statSemWait
            - -statTiming
            - -statNotifQueue
          env:
            - name: ORIONLD_MONGOCONLY
              value: "TRUE"
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: fiware-orionld-secret
                  key: db-password
            - name: API_KEY
              valueFrom:
                secretKeyRef:
                  name: fiware-orionld-secret
                  key: api-key
          ports:
            - name: http
              containerPort: 1026
              protocol: TCP
          resources:
            requests:
              cpu: 200m
              memory: 256Mi
            limits:
              cpu: 1
              memory: 512Mi
          livenessProbe:
            httpGet:
              path: /version
              port: http
            initialDelaySeconds: 10
            periodSeconds: 5
            timeoutSeconds: 2
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /version
              port: http
            initialDelaySeconds: 5
            periodSeconds: 5
            timeoutSeconds: 2
            failureThreshold: 3
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop:
                - ALL
      restartPolicy: Always
      dnsPolicy: ClusterFirst

---
# 4) HPA ajustado
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
  minReplicas: 3
  maxReplicas: 15
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 50
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 70
```

Para aplicar:

1) `kubectl -n teste-orion delete deployment/fiware-orionld`  
2) `kubectl apply -f corrected-fiware-orionld.yaml`  

Isso garantirá que todos os campos, seletores e credenciais estejam consistentes e alinhados com boas práticas de produção.

## 📋 Estado Final do Namespace (teste-orion)
```
NAME                                  READY   STATUS         RESTARTS   AGE
pod/fiware-orionld-5f9f8dc9ff-4n977   0/1     ErrImagePull   0          63s
pod/fiware-orionld-5f9f8dc9ff-fkfzn   0/1     ErrImagePull   0          63s
pod/fiware-orionld-5f9f8dc9ff-smkzl   0/1     ErrImagePull   0          63s

NAME                             TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)          AGE
service/fiware-orionld-service   LoadBalancer   10.111.158.0   <pending>     1027:32323/TCP   2m26s

NAME                             READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/fiware-orionld   0/3     3            0           63s

NAME                                        DESIRED   CURRENT   READY   AGE
replicaset.apps/fiware-orionld-5f9f8dc9ff   3         3         0       63s

NAME                                                     REFERENCE                   TARGETS              MINPODS   MAXPODS   REPLICAS   AGE
horizontalpodautoscaler.autoscaling/fiware-orionld-hpa   Deployment/fiware-orionld   cpu: <unknown>/50%   3         15        3          2m26s
```