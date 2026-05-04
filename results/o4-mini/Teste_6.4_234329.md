# Relatório de Benchmark: 6-selenium.yaml

* **Modelo:** `o4-mini`
* **Rodada:** 4
* **Status Final:** ❌ FALHA
* **HealthCheck:** Falha Crítica no Pod selenium-hub-68ff644d59-hmdd9: ErrImagePull

## 🧠 Raciocínio do Agente
Segue o diagnóstico dos recursos atuais e as correções propostas para alinhar seu Deployment e Service às melhores práticas em produção.

1) Service:  
   Problema: selector com typo “sellenium-hub” (fica sem match com pods “selenium-hub”).  
   Correção: ajustar selector para app=selenium-hub.  

2) Service: tipo NodePort expõe portas arbitrárias no nó; em produção costuma-se usar LoadBalancer (ou ClusterIP + Ingress) para tráfego controlado.  
   Correção: alterar type para LoadBalancer (ou ClusterIP se houver Ingress upstream).  

3) Deployment – Imagem sem tag fixa.  
   Correção: usar uma tag de versão (ex: selenium/hub:4.9.1) para garantir imutabilidade.  

4) Deployment – Credenciais em variáveis plaintext.  
   Correção: mover GRID_HUB_PASSWORD e DATABASE_URL para Secret e referenciar via secretKeyRef.  

5) Deployment – Requests ausentes. Só há limits de CPU e memória.  
   Correção: adicionar requests (ex: cpu: 250m, memory: 512Mi).  

6) Deployment – securityContext vazio, sem restrições de usuário.  
   Correção: definir runAsNonRoot: true, dropCapabilities, readOnlyRootFilesystem etc.  

7) (Opcional) Deployment – falta tolerância a falhas planejadas (PodDisruptionBudget) e anti-affinity.  

Abaixo manifest limpo e corrigido para aplicação (namespace “teste-selenium”):  

```yaml
---
apiVersion: v1
kind: Secret
metadata:
  name: selenium-hub-secrets
  namespace: teste-selenium
type: Opaque
stringData:
  GRID_HUB_PASSWORD: selenium-admin-2024
  DATABASE_URL: postgres://user:pass@localhost/selenium
---
apiVersion: v1
kind: Service
metadata:
  name: selenium-hub
  namespace: teste-selenium
  labels:
    app: selenium-hub
spec:
  type: LoadBalancer          # em produção, use LoadBalancer ou ClusterIP+Ingress
  selector:
    app: selenium-hub         # corrigido typo
  ports:
    - name: http
      port: 4444
      targetPort: 4444
      protocol: TCP
    - name: https
      port: 4443
      targetPort: 4443
      protocol: TCP
    - name: node
      port: 4442
      targetPort: 4442
      protocol: TCP
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: selenium-hub
  namespace: teste-selenium
  labels:
    app: selenium-hub
spec:
  replicas: 2                          # aumentar para alta disponibilidade
  selector:
    matchLabels:
      app: selenium-hub
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%
      maxUnavailable: 25%
  template:
    metadata:
      labels:
        app: selenium-hub
    spec:
      securityContext:
        runAsNonRoot: true
        fsGroup: 1000
      containers:
        - name: selenium-hub
          image: selenium/hub:4.9.1    # tag fixa
          imagePullPolicy: IfNotPresent
          env:
            - name: GRID_HUB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: selenium-hub-secrets
                  key: GRID_HUB_PASSWORD
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: selenium-hub-secrets
                  key: DATABASE_URL
          ports:
            - containerPort: 4444
            - containerPort: 4443
            - containerPort: 4442
            - containerPort: 65000
          resources:
            requests:
              cpu: 250m
              memory: 512Mi
            limits:
              cpu: 500m
              memory: 1000Mi
          livenessProbe:
            httpGet:
              path: /wd/hub/status
              port: 4444
            initialDelaySeconds: 30
            periodSeconds: 10
            timeoutSeconds: 5
            successThreshold: 1
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /wd/hub/status
              port: 4444
            initialDelaySeconds: 30
            periodSeconds: 10
            timeoutSeconds: 5
            successThreshold: 1
            failureThreshold: 3
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
      dnsPolicy: ClusterFirst
      restartPolicy: Always
      terminationGracePeriodSeconds: 30
```

Executando `kubectl apply -f` desse manifesto no namespace “teste-selenium” você terá:
- Secret criado/atualizado
- Service corrigido (selector + tipo)
- Deployment com boas práticas de segurança, recursos e imutabilidade de imagem.

## 📋 Estado Final do Namespace (teste-selenium)
```
NAME                                READY   STATUS         RESTARTS   AGE
pod/selenium-hub-5469ddb6dd-hpqg8   1/1     Running        0          57s
pod/selenium-hub-5469ddb6dd-tzlbj   0/1     Running        0          17s
pod/selenium-hub-68ff644d59-hmdd9   0/1     ErrImagePull   0          17s

NAME                   TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)                                AGE
service/selenium-hub   ClusterIP   10.110.41.185   <none>        4444/TCP,4443/TCP,4442/TCP,65000/TCP   57s

NAME                           READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/selenium-hub   1/2     1            1           57s

NAME                                      DESIRED   CURRENT   READY   AGE
replicaset.apps/selenium-hub-5469ddb6dd   2         2         1       57s
replicaset.apps/selenium-hub-68ff644d59   1         1         0       17s
```