# Relatório de Benchmark: 10-mongodb.yaml

* **Modelo:** `o4-mini`
* **Rodada:** 3
* **Status Final:** ❌ FALHA
* **HealthCheck:** Timeout: Os recursos não atingiram estabilidade no tempo previsto

## 🧠 Raciocínio do Agente
Segue a análise dos recursos atuais e as recomendações de melhoria para um ambiente de produção:

1) Service “mongodb-service”  
   Problema: o selector aponta para `app: nonexistent-mongodb`, que não corresponde aos pods do Deployment (`app: mongodb-app`).  
   Impacto: nenhuma conexão ao MongoDB porque o Service não encontra endpoints.  
   Correção recomendada: alinhar o selector com as labels do Pod (use `app: mongodb-app`).

2) Deployment “mongodb-deployment”  
   a) Imagem sem tag fixa  
      Uso atual: `image: mongo` (puxa “latest”).  
      Risco: quebra de compatibilidade em atualizações inopinadas.  
      Correção: usar uma versão sem “latest”, ex. `mongo:6.0.5`.  
   b) Volume de dados em emptyDir  
      Uso atual: `emptyDir` → dados perdidos ao reiniciar o pod.  
      Recomendações:  
        • Criar PersistentVolumeClaim (PVC) dinâmico com StorageClass que suporte resize e montar em `/data/db`.  
        • Remover `emptyDir`.  
   c) Falta de probes de saúde  
      Sem liveness/readiness, o kubelet não detecta falhas do Mongo.  
      Correção:  
        • LivenessProbe HTTP/TCP ou exec:  
            exec: [`mongo`, `--eval`, `db.adminCommand('ping')`]  
            initialDelaySeconds: 30, periodSeconds: 10, timeoutSeconds: 5  
        • ReadinessProbe similar (timeout menor).  
   d) Recursos (CPU/mem) não definidos  
      Sem requests/limits, scheduling e QoS ficam indefinidos.  
      Sugestão:  
        resources:  
          requests: { cpu: “100m”, memory: “256Mi” }  
          limits:   { cpu: “500m”, memory: “1Gi” }  
   e) Credenciais inline no Deployment  
      As senhas de root estão em plaintext nos YAMLs e no History do cluster.  
      Correção:  
        • Criar Secret (tipo Opaque) para usuário/senha  
        • No Pod, referenciar via `envFrom: secretRef`.

3) PVC “mongo-data-pvc”  
   Status atual: provavelmente foi provisionado com StorageClass que não permite expansão, portanto o patch de 20Gi falhou.  
   Ações:  
     • *(Opcional)* recriar PVC com `storageClassName` dinâmico que suporte resize antes de dimensionar.  
     • Ou manter o tamanho atual, sem tentar patch de resize.

—  
Abaixo um manifesto unificado corrigido; aplique primeiro em dry-run (`--server-dry-run`) e depois efetive:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: mongodb-secret
  namespace: teste-mongodb
type: Opaque
stringData:
  MONGO_INITDB_ROOT_USERNAME: admin
  MONGO_INITDB_ROOT_PASSWORD: SecurePassword123!

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mongo-data-pvc
  namespace: teste-mongodb
  labels:
    app: mongodb-app
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 20Gi
  storageClassName: standard  # validar se suporta resize dinamicamente

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
      protocol: TCP
      port: 27017
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
  replicas: 1
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
      containers:
        - name: mongodb
          image: mongo:6.0.5
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 27017
          envFrom:
            - secretRef:
                name: mongodb-secret
          # opcional: montar variável de URL caso precise
          # env:
          #   - name: MONGODB_URL
          #     value: mongodb://$(MONGO_INITDB_ROOT_USERNAME):$(MONGO_INITDB_ROOT_PASSWORD)@mongodb-service:27017/admin
          volumeMounts:
            - name: mongo-data
              mountPath: /data/db
          resources:
            requests:
              cpu: "100m"
              memory: "256Mi"
            limits:
              cpu: "500m"
              memory: "1Gi"
          livenessProbe:
            exec:
              command:
                - mongo
                - --eval
                - db.adminCommand('ping')
            initialDelaySeconds: 30
            periodSeconds: 10
            timeoutSeconds: 5
          readinessProbe:
            exec:
              command:
                - mongo
                - --eval
                - db.adminCommand('ping')
            initialDelaySeconds: 10
            periodSeconds: 5
            timeoutSeconds: 3
      volumes:
        - name: mongo-data
          persistentVolumeClaim:
            claimName: mongo-data-pvc
```

Passos finais:  
1. `kubectl apply -f corrected-mongodb.yaml --server-dry-run`  
2. Se OK, `kubectl apply -f corrected-mongodb.yaml`  

Com isso corrigimos selectors, segurança, armazenamento persistente, probes e recursos de CPU/memória.

## 📋 Estado Final do Namespace (teste-mongodb)
```
NAME                                      READY   STATUS              RESTARTS   AGE
pod/mongodb-deployment-54cdd84c87-7gnzh   0/1     Terminating         0          3m22s
pod/mongodb-deployment-54cdd84c87-bkfxn   0/1     Terminating         0          3m22s
pod/mongodb-deployment-5974cb9594-csrqr   0/1     Terminating         0          3m34s
pod/mongodb-deployment-5974cb9594-mgtwm   0/1     Terminating         0          3m22s
pod/mongodb-deployment-59cfdbf774-84cnb   0/1     Terminating         0          2m53s
pod/mongodb-deployment-59cfdbf774-qdwp6   0/1     Terminating         0          2m53s
pod/mongodb-deployment-5bc6d6767b-m89pn   0/1     Terminating         0          4m19s
pod/mongodb-deployment-5df7997b44-9642z   0/1     Terminating         0          2m54s
pod/mongodb-deployment-5df7997b44-jqvff   0/1     Terminating         0          3m8s
pod/mongodb-deployment-6488b8675-k6ln6    0/1     ContainerCreating   0          2m12s
pod/mongodb-deployment-7b567db55c-npfzn   0/1     Error               0          4m54s
pod/mongodb-deployment-7cdd8dcbf7-lhq5l   0/1     Terminating         0          2m43s
pod/mongodb-deployment-7cdd8dcbf7-ltq6l   0/1     Terminating         0          2m43s
pod/mongodb-deployment-7f4cc9bf77-4gwjh   0/1     Terminating         0          4m40s
pod/mongodb-deployment-86b6fb67df-4klxj   0/1     ContainerCreating   0          2m23s

NAME                      TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)     AGE
service/mongodb-service   ClusterIP   10.106.166.251   <none>        27017/TCP   5m42s

NAME                                 READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/mongodb-deployment   0/1     1            0           5m42s

NAME                                            DESIRED   CURRENT   READY   AGE
replicaset.apps/mongodb-deployment-54cdd84c87   0         0         0       3m22s
replicaset.apps/mongodb-deployment-559d9986d4   0         0         0       5m42s
replicaset.apps/mongodb-deployment-5974cb9594   0         0         0       3m34s
replicaset.apps/mongodb-deployment-59cfdbf774   0         0         0       2m54s
replicaset.apps/mongodb-deployment-5bc6d6767b   0         0         0       4m19s
replicaset.apps/mongodb-deployment-5df7997b44   0         0         0       3m8s
replicaset.apps/mongodb-deployment-6488b8675    1         1         0       2m12s
replicaset.apps/mongodb-deployment-7b567db55c   0         0         0       4m54s
replicaset.apps/mongodb-deployment-7cdd8dcbf7   0         0         0       2m43s
replicaset.apps/mongodb-deployment-7f4cc9bf77   0         0         0       4m40s
replicaset.apps/mongodb-deployment-7f55b897d4   0         0         0       5m9s
replicaset.apps/mongodb-deployment-86b6fb67df   1         1         0       2m23s
replicaset.apps/mongodb-deployment-8c498576d    0         0         0       4m32s
```