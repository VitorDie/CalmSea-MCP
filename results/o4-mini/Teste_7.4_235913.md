# Relatório de Benchmark: 7-elasticsearch.yaml

* **Modelo:** `o4-mini`
* **Rodada:** 4
* **Status Final:** ❌ FALHA
* **HealthCheck:** Timeout: Os recursos não atingiram estabilidade no tempo previsto

## 🧠 Raciocínio do Agente
Segue análise dos recursos atuais e proposta de correções.

1) Service “elasticsearch”  
   Problemas detectados  
   - Selector mismatches: o Service usa `selector: component=elasticsearch`, o Deployment marca pods com `app=elasticsearch`. Com isso não há endpoints no Service.  
   - O Service é LoadBalancer expondo também a porta 9300 (cluster-internal transport). Em geral deixa-se o transport em ClusterIP interno ou em um Service separado.  
   - Falta `externalTrafficPolicy: Local` (se você precisar preservar IP de cliente) e anotações de health-check do LB (dependendo do cloud-provider).  

   Sugestões de correção  
   - Unificar labels/selectors usando `app: elasticsearch` em Service e Deployment.  
   - Manter no LoadBalancer só a porta HTTP (9200); deixar 9300 em um Service de tipo ClusterIP ou removê-la do LB.  
   - Adicionar `externalTrafficPolicy: Local` se for preservar IP de origem.  

   YAML proposto:
   apiVersion: v1
   kind: Service
   metadata:
     name: elasticsearch
     namespace: teste-elasticsearch
     labels:
       app: elasticsearch
   spec:
     type: LoadBalancer
     externalTrafficPolicy: Local
     selector:
       app: elasticsearch
     ports:
       - name: http
         port: 9200
         targetPort: 9200
         protocol: TCP
   ---
   apiVersion: v1
   kind: Service
   metadata:
     name: elasticsearch-transport
     namespace: teste-elasticsearch
     labels:
       app: elasticsearch
   spec:
     type: ClusterIP
     selector:
       app: elasticsearch
     ports:
       - name: transport
         port: 9300
         targetPort: 9300
         protocol: TCP

2) Deployment “elasticsearch”  
   Problemas detectados  
   - Está setada a variável `discovery.type=single-node`, mas a spec pede `replicas: 3`. Num cluster ES de 3 nós você precisa de configurações de discovery adequadas (seed_hosts, initial_master_nodes) ou reduzir para 1 réplica.  
   - Valores de Xms/Xmx (`1g`) não correspondem aos requests/limits atuais (requests 500 m /2 Gi, limits 1/4 Gi). Em produção é melhor alocar ~50% da memória container ao JVM heap e ajustar requests/limits em sintonia.  
   - Falta `runAsNonRoot`, `runAsUser`, `terminationGracePeriodSeconds` mais longo e um `preStop` para shutdown seguro do Elasticsearch.  
   - Não existe request/limit para `ephemeral-storage`. Em produção é recomendável pedir e limitar também esse recurso.  
   - Probes OK, mas o readiness poderia aguardar pelo cluster atingir ao menos “yellow” e ter um timeout mais longo.  

   Sugestões de correção  
   - Configurar discovery para três nós: usar env vars `cluster.initial_master_nodes` e `discovery.seed_hosts`.  
   - Ajustar ES_JAVA_OPTS para 50% da memória real do pod (ex: -Xms2g -Xmx2g se requests=4Gi).  
   - Incluir `securityContext` de pod e container, `terminationGracePeriodSeconds: 120`, e um `lifecycle.preStop` que chame `elasticsearch-node shutdown`.  
   - Declarar requests/limits de ephemeral-storage.  

   YAML proposto:
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: elasticsearch
     namespace: teste-elasticsearch
     labels:
       app: elasticsearch
   spec:
     replicas: 3
     selector:
       matchLabels:
         app: elasticsearch
     strategy:
       type: RollingUpdate
       rollingUpdate:
         maxSurge: 1
         maxUnavailable: 1
     template:
       metadata:
         labels:
           app: elasticsearch
       spec:
         terminationGracePeriodSeconds: 120
         securityContext:
           fsGroup: 1000
           runAsUser: 1000
           runAsGroup: 1000
         affinity:
           podAntiAffinity:
             requiredDuringSchedulingIgnoredDuringExecution:
             - labelSelector:
                 matchLabels:
                   app: elasticsearch
               topologyKey: kubernetes.io/hostname
         containers:
         - name: elasticsearch
           image: docker.elastic.co/elasticsearch/elasticsearch:7.17.0
           imagePullPolicy: IfNotPresent
           env:
           - name: cluster.name
             value: elasticsearch-cluster
           - name: node.name
             valueFrom:
               fieldRef:
                 fieldPath: metadata.name
           - name: discovery.seed_hosts
             value: "elasticsearch-0,elasticsearch-1,elasticsearch-2"
           - name: cluster.initial_master_nodes
             value: "elasticsearch-0,elasticsearch-1,elasticsearch-2"
           - name: ES_JAVA_OPTS
             value: "-Xms2g -Xmx2g"
           ports:
           - containerPort: 9200
             name: http
             protocol: TCP
           - containerPort: 9300
             name: transport
             protocol: TCP
           livenessProbe:
             httpGet:
               path: /
               port: 9200
               scheme: HTTP
             initialDelaySeconds: 60
             periodSeconds: 10
             timeoutSeconds: 5
             failureThreshold: 5
           readinessProbe:
             httpGet:
               path: "/_cluster/health?wait_for_status=yellow&timeout=1s"
               port: 9200
               scheme: HTTP
             initialDelaySeconds: 60
             periodSeconds: 10
             timeoutSeconds: 5
             failureThreshold: 3
           resources:
             requests:
               cpu: "1"
               memory: "4Gi"
               ephemeral-storage: "20Gi"
             limits:
               cpu: "2"
               memory: "8Gi"
               ephemeral-storage: "50Gi"
           volumeMounts:
           - name: data
             mountPath: /usr/share/elasticsearch/data
           lifecycle:
             preStop:
               exec:
                 command: ["/bin/sh","-c","bin/elasticsearch-node shutdown --quiet"]
         volumes:
         - name: data
           persistentVolumeClaim:
             claimName: elasticsearch-pvc

3) PVC “elasticsearch-pvc”  
   - Não conseguimos extrair detalhes via ferramenta, mas em produção certifique-se de:
     • ter `storageClassName` adequado (de preferência replicado e rápido)  
     • `accessModes: [ "ReadWriteOnce" ]`  
     • `resources.requests.storage` suficiente (ex: 200Gi+)  

Como próximos passos aplique os manifestos acima (usando `kubectl apply --dry-run=client` para validação) e verifique logs/probes até os pods ficarem prontos.

## 📋 Estado Final do Namespace (teste-elasticsearch)
```
NAME                                 READY   STATUS        RESTARTS   AGE
pod/elasticsearch-7ddcffb77f-dczbl   0/1     Terminating   0          3m14s
pod/elasticsearch-85bb68c99b-8c2bh   0/1     Pending       0          2m28s

NAME                       DESIRED   CURRENT   READY   AGE
replicationcontroller/es   1         0         0       3m50s

NAME                    TYPE           CLUSTER-IP       EXTERNAL-IP   PORT(S)                         AGE
service/elasticsearch   LoadBalancer   10.107.206.207   <pending>     9200:32220/TCP,9300:30780/TCP   3m50s

NAME                            READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/elasticsearch   0/1     1            0           3m14s

NAME                                       DESIRED   CURRENT   READY   AGE
replicaset.apps/elasticsearch-757dc68955   0         0         0       2m57s
replicaset.apps/elasticsearch-7ddcffb77f   0         0         0       3m14s
replicaset.apps/elasticsearch-85bb68c99b   1         1         0       2m28s
```