# Relatório de Benchmark: 10-mongodb.yaml

* **Modelo:** `o4-mini`
* **Rodada:** 1
* **Status Final:** ❌ FALHA
* **HealthCheck:** Falha Crítica no Pod mongodb-deployment-5fb7899779-v898h: CreateContainerConfigError

## 🧠 Raciocínio do Agente
Segue a análise dos recursos atuais e as recomendações de melhoria para um ambiente de produção, bem como os manifestos atualizados levando em conta as boas práticas.

1) Service “mongodb‐service”  
   Problema  
   - selector: `app: nonexistent-mongodb` não corresponde ao label do Pod (`app: mongodb-app`), logo não há endpoints.  
   Sugestão  
   - Alinhar selector do Service com o label do Deployment (`app: mongodb-app`).  

2) Deployment “mongodb‐deployment”  
   a) Storage  
   - Usa `emptyDir` (volátil) em vez de PVC. Em produção é necessário um volume persistente.  
   - Já foi criado um PersistentVolumeClaim `mongodb-pvc`, mas o spec ainda monta `emptyDir`.  
   Sugestão  
   - Substituir `emptyDir` pelo PVC.  

   b) Imagem  
   - Atualmente `image: mongo` (latest).  
   Sugestão  
   - Definir tag fixa (ex: `mongo:6.0.4`).  

   c) Credenciais  
   - `MONGO_INITDB_ROOT_USERNAME` e `MONGO_INITDB_ROOT_PASSWORD` hardcoded no YAML.  
   Sugestão  
   - Armazenar em Secret e usar `valueFrom`.  

   d) Recursos  
   - Não há `resources.requests/limits`.  
   Sugestão  
   - Definir valores apropriados (ex: requests.cpu/memory e limits).  

   e) Segurança  
   - Sem securityContext no Pod/Container.  
   Sugestão  
   - Usar `runAsNonRoot`, `fsGroup`, e `securityContext` para o container.  

   f) Health probes  
   - Não há liveness/readiness probes.  
   Sugestão  
   - Adicionar probes baseadas em TCP ou comando.  

   g) Políticas de reinício  
   - RollingUpdate padrão OK, só ajustar se necessário.  

---  
Abaixo um manifesto consolidado com as correções:

```yaml
---
apiVersion: v1
kind: Service
metadata:
  name: mongodb-service
  namespace: teste-mongodb
  labels:
    app: mongodb-app
spec:
  type: ClusterIP
  selector:
    app: mongodb-app
  ports:
    - name: mongodb
      port: 27017
      protocol: TCP
      targetPort: 27017
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mongodb-deployment
  namespace: teste-mongodb
  labels:
    app: mongodb-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: mongodb-app
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: mongodb-app
    spec:
      securityContext:
        runAsNonRoot: true
        fsGroup: 1000
      containers:
      - name: mongodb
        image: mongo:6.0.4
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 27017
        env:
        - name: MONGO_INITDB_ROOT_USERNAME
          valueFrom:
            secretKeyRef:
              name: mongodb-secret
              key: username
        - name: MONGO_INITDB_ROOT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mongodb-secret
              key: password
        - name: MONGODB_URL
          value: "mongodb://$(MONGO_INITDB_ROOT_USERNAME):$(MONGO_INITDB_ROOT_PASSWORD)@mongodb-service:27017/admin"
        volumeMounts:
        - name: mongo-storage
          mountPath: /data/db
        resources:
          requests:
            cpu: "100m"
            memory: "256Mi"
          limits:
            cpu: "500m"
            memory: "1Gi"
        readinessProbe:
          tcpSocket:
            port: 27017
          initialDelaySeconds: 10
          periodSeconds: 10
          failureThreshold: 3
        livenessProbe:
          exec:
            command:
            - mongo
            - --eval
            - "db.adminCommand('ping')"
          initialDelaySeconds: 30
          periodSeconds: 20
      volumes:
      - name: mongo-storage
        persistentVolumeClaim:
          claimName: mongodb-pvc
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mongodb-pvc
  namespace: teste-mongodb
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: standard
---
apiVersion: v1
kind: Secret
metadata:
  name: mongodb-secret
  namespace: teste-mongodb
type: Opaque
data:
  # echo -n "admin"           | base64
  username: YWRtaW4=
  # echo -n "SecurePassword123!" | base64
  password: U2VjdXJlUGFzc3dvcmQxMjMh
```

Para aplicar:

1. Se desejar fazer dry-run e validação de esquema:  
   kubectl apply -f manifest.yaml --namespace teste-mongodb --dry-run=client  

2. Se aprovado, execute sem --dry-run.  

Assim garantimos consistência de selector, storage persistente, segurança, controle de recursos e observabilidade via probes.

## 📋 Estado Final do Namespace (teste-mongodb)
```
NAME                                      READY   STATUS                       RESTARTS   AGE
pod/mongodb-deployment-559d9986d4-8rw5h   1/1     Running                      0          2m27s
pod/mongodb-deployment-559d9986d4-j25n5   1/1     Running                      0          2m2s
pod/mongodb-deployment-559d9986d4-lh7zf   1/1     Running                      0          2m2s
pod/mongodb-deployment-5fb7899779-v898h   0/1     CreateContainerConfigError   0          2m2s

NAME                      TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)     AGE
service/mongodb-service   ClusterIP   10.100.208.57   <none>        27017/TCP   2m27s

NAME                                 READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/mongodb-deployment   3/3     1            3           2m27s

NAME                                            DESIRED   CURRENT   READY   AGE
replicaset.apps/mongodb-deployment-559d9986d4   3         3         3       2m27s
replicaset.apps/mongodb-deployment-5fb7899779   1         1         0       2m2s
```