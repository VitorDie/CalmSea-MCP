# AgentK - Especialista em Configurações YAML Kubernetes

AgentK é um assistente inteligente especializado em **análise, otimização e gestão de configurações YAML do Kubernetes**. Utilizando GPT-4.1 e MCP (Model Context Protocol), oferece orientações baseadas em boas práticas para criação e manutenção de recursos Kubernetes de qualidade profissional.

<p align="center">
  <img src="docs/AgentK-white.png" alt="AgentK" width="150" />
</p>

## Objetivo Principal

**AgentK é seu consultor especializado em YAML Kubernetes**, focado em:
- **Extrair e analisar** configurações existentes do cluster
- **Sugerir melhorias** baseadas em boas práticas de produção
- **Validar configurações** antes da aplicação (dry-run)
- **Implementar recursos** com verificação automática de conflitos
- **Orientar na criação** de YAMLs seguindo padrões de qualidade

> **Importante**: AgentK **não é uma ferramenta de monitoramento**, mas sim um especialista em configurações YAML e aplicação de boas práticas.

## Capacidades Principais

### Gestão Completa de Recursos (CRUD)
- **Listar** recursos do cluster por tipo
- **Extrair** configurações YAML de recursos existentes  
- **Obter** YAML específico por nome e namespace
- **Implementar** recursos (create/update automático com prevenção de conflitos)
- **Deletar** recursos individuais do cluster
- **Validar** YAMLs com dry-run antes da aplicação

### Foco em Boas Práticas
- **Labels e annotations** consistentes
- **Resource limits e requests** adequados
- **Configurações de segurança** apropriadas 
- **Estrutura YAML** limpa e legível

### Recursos Suportados
- **Namespaced**: `pods`, `services`, `deployments`, `configmaps`, `secrets`, `ingresses`, `persistent_volume_claims`, `replicasets`, `statefulsets`, `cronjobs`, `jobs`, `horizontal_pod_autoscalers`, `replication_controllers`, `daemon_sets`  
- **Cluster-wide**: `nodes`, `persistent_volumes`, `namespaces`

### Exportação de Histórico
- **Relatórios em Markdown** com estatísticas da sessão
- **Métricas de performance** (tempo de execução, tokens utilizados)
- **Histórico completo** de conversas e chamadas MCP

## 🚀 Tecnologias

- **FastMCP** + **Kubernetes Python Client** (Servidor)
- **Streamlit** + **GPT-4** (Cliente)
- **6 MCP Tools** para operações CRUD completas
- **Configuração Externa** (`resource_config.yaml`)

## 🛠️ Setup e Execução (AgentK) 

### Pré-requisitos
- Docker e Docker Compose instalados
- Acesso a um cluster Kubernetes (`kubectl` configurado)
- Chave de API da OpenAI

### 1. Variáveis de Ambiente 

```bash
# 1. Clone e configure
git clone https://github.com/VitorDie/AgentK-MCP.git
cd AgentK-MCP
```

```bash
# 1. crie o arquivo .env
touch .env
# 2. Edite o arquivo .env recém-criado e insira a sua chave da OpenAI:
echo "OPENAI_API_KEY=sk-sua-chave-aqui" >> .env
```

### 2. Infraestrutura Kubernetes (Minikube e Túnel SSH)

Para que o AgentK atue no cluster, precisamos apontar os certificados corretamente. O projeto utiliza uma arquitetura agnóstica através da pasta certs-remotos/.

### A. Extraindo os Certificados:

***Se o Minikube for local:***

```bash
mkdir -p certs-remotos
cp ~/.minikube/ca.crt ~/.minikube/profiles/minikube/client.{crt,key} ./certs-remotos/
```

***Se o Minikube estiver em uma VM remota:***

```bash
mkdir -p certs-remotos
scp -i ~/.ssh/sua_chave usuario@IP_DA_VM:~/.minikube/ca.crt usuario@IP_DA_VM:~/.minikube/profiles/minikube/client.{crt,key} ./certs-remotos/
```

### B. Configurando o Kubeconfig Remoto:

```bash
# 1. Copie o arquivo de template fornecido no repositório:
cp remote-kubeconfig.example.yaml remote-kubeconfig.yaml
```

```bash
# 2. Abra o remote-kubeconfig.yaml e altere a linha server de acordo com o seu ambiente:
```

```bash
# MINIKUBE LOCAL
Em remote-kubeconfig.yaml use o IP interno da rede Docker (descubra com kubectl cluster-info). Ex: server: https://192.168.49.2:8443
```

```bash
# MINIKUBE EM VM REMOTA
# Crie um túnel SSH para a sua máquina local e aponte para o localhost, e mantenha ele aberto enquanto estiver usando a aplicação:
ssh -L 0.0.0.0:6443:[IP_INTERNO_MINIKUBE]:[PORTA_INTERNA] usuario@IP_DA_VM -N -f

# Você roda o kubectl cluster-info lá dentro da VM e pega o resultado (ex: 192.168.49.2). 
# Depois, no seu terminal local, você sobe o túnel com os seus dados reais:
ssh -i .ssh/gcp_agentk -L 0.0.0.0:6443:192.168.49.2:8443 agentk@10.128.0.2 -N -f

Neste caso, em remote-kubeconfig.yaml mantenha o arquivo com server: https://localhost:6443.
```

### 3. Rodando os Serviços (Docker Compose)

Com a infraestrutura de rede e credenciais prontas, você pode levantar os serviços utilizando o Docker Compose como orquestrador.

### Interface Principal do Agente (Modo Interativo):

Inicia o assistente e o servidor MCP integrados.

```bash
docker compose build --no-cache agentk
docker compose up agentk
```

### Testes Unitários:

Executa a suíte de testes de forma isolada, validando a lógica das ferramentas e do Collector.

```bash
docker compose run --rm tests-unit
```

### Testes de Integração:

Executa o fluxo completo do Agente K8s batendo na API real do Minikube configurado.

```bash
docker compose run --rm tests-integration
```

### Executando o Teste de Performance (Benchmark)

O serviço de performance é responsável por rodar os testes de carga e análise de vulnerabilidades em lote, essencial para a coleta de métricas (Duração, Tokens consumidos, Acurácia).

```bash
# 1. Execute o container dedicado ao benchmark:
docker compose build --no-cache performancetest

# EXECUÇAO COM OLLAMA

## AMD

docker compose --profile amd up -d performancetest

## NVIDIA

docker compose --profile nvidia up -d performancetest

## ver log de execução

docker logs -f performance-test

# EXECUÇÃO UTILIZANDO APENAS OPENAI

docker compose up -d ollama-cpu servermcp
docker compose up performancetest

# 2. Coleta de Dados: 
# Os resultados de cada iteração, incluindo os prompts completos e as respostas do LLM, serão gravados em tempo real no arquivo results/benchmark_master.csv.
```


## Principais Diferenciais

- **Boas Práticas Integradas**: Sugestões de melhorias automáticas
- **Dry-run Integrado**: Validação antes da aplicação
- **Interface Conversacional**: Interação natural via chat
- **Configuração Externa**: Flexibilidade e customização

## 🏗️ Arquitetura

<p align="center">
  <img src="docs/agent-k-arch.png" alt="AgentK" width="500" />
</p>

## 📚 Documentação Completa

### 📖 Guias de Configuração e Deploy
- **[Configuração do Ambiente na VM](docs/VM-environment-config.md)** - Setup completo do ambiente de produção
- **[Pipeline CI/CD com GitHub Actions](docs/Pipeline-GithubActions-deployment-config.md)** - Deploy automático e rollback

### 🧪 Testes e Validação
- **[Procedimento de Testes do AgentK](docs/Procedimento-Testes-AgentK.md)** - Metodologia completa dos 50 testes realizados
- **[Arquivos de Teste YAML](docs/tests/)** - 10 arquivos com misconfigurations + 50 resultados exportados

### 📊 Resultados e Métricas
**Taxa de Detecção:**
- ✅ Credenciais Expostas: **100%** (50/50)
- ✅ Versão de Imagem: **100%** (50/50)
- ✅ Erros Semânticos: **96%** (48/50)

**Taxa de Implementação:** **88%** (44/50 testes bem-sucedidos)

**AgentK - Exemplo de uso** 
<p align="center">
  <img src="docs/images/AgentK-Frontend.jpeg" alt="AgentK" width="600" />
</p>

### 🎨 Recursos Visuais
- **[Arquitetura do Sistema](docs/agent-k-arch.png)** - Diagrama da arquitetura MCP
- **[Exemplos de YAML](docs/)** - `basic-example.yaml` e `orion-example.yaml`

### 🔗 Links Rápidos
| Documento | Descrição |
|-----------|-----------|
| [Procedimento de Testes](docs/Procedimento-Testes-AgentK.md) | Metodologia, resultados e análise dos 50 testes |
| [Resultados dos Testes](docs/tests/results/) | 50 sessões exportadas com timestamps |
| [VM Setup](docs/VM-environment-config.md) | Configuração do ambiente de produção |
| [CI/CD Pipeline](docs/Pipeline-GithubActions-deployment-config.md) | Deploy automatizado com GitHub Actions |

---

**Orientador:** Professor Dr. Fábio Henrique Cabrini  
**Instituição:** Faculdade Engenheiro Salvador Arena

---
