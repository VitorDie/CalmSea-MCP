import os
import time
from datetime import datetime
from src.application.services.agent_service import AgentService
from src.infrastructure.llm.openai_adapter import OpenAIAdapter
from src.infrastructure.llm.ollama_adapter import OllamaAdapter
from src.adapters.llm.metrics_decorator import LLMMonitorDecorator
from src.infrastructure.k8s_adapter.service import K8sServiceAdapter
from src.infrastructure.metrics.collector import TCCMetricsCollector
from src.infrastructure.k8s_adapter.scenario_manager import K8sScenarioManager
from src.infrastructure.k8s_adapter.health_checker import K8sHealthChecker

class PerformanceTestRunner:
    def __init__(self):
        self.models = ["llama3.1"]
        self.yamls = [
            "1-orion.yaml", "2-frontend.yaml", "3-mysql.yaml", "4-vllm.yaml", 
            "5-nginx.yaml", "6-selenium.yaml", "7-elasticsearch.yaml", 
            "8-newrelic.yaml", "9-storm.yaml", "10-mongodb.yaml", "fiware-minikube.yaml"
        ]
        self.reps = 1
        self.collector = TCCMetricsCollector()
        self.env_mgr = K8sScenarioManager()
        self.health = K8sHealthChecker()

    def get_agent(self, model_name):
        k8s = K8sServiceAdapter()
        if "o4" in model_name:
            adapter = OpenAIAdapter(model=model_name)
            provider = "OpenAI"
        else:
            adapter = OllamaAdapter(model=model_name)
            provider = "Ollama"
        
        monitored_llm = LLMMonitorDecorator(adapter, provider, self.collector)
        return AgentService(llm_provider=monitored_llm, k8s_adapter=k8s)

    def run(self):
        for model in self.models:
            output_dir = f"results/{model.replace(':', '-')}"
            os.makedirs(output_dir, exist_ok=True)

            for yaml_file in self.yamls:
                # 1. Setup K8s (Cria o ringue de teste)
                ns = self.env_mgr.prepare(yaml_file)
                time.sleep(5) # Tempo para o K8s processar o namespace
                
                # 2. Captura o YAML Vivo (O que a IA vai auditar)
                live_yaml = self.env_mgr.get_live_yaml(ns, f"docs/tests/scenarios/{yaml_file}")

                # 3. Agente (O Decorator chama o record() e preenche o buffer aqui)
                agent = self.get_agent(model)
                sys_instruction = (
                    "Você é um Auditor de Segurança K8s. Analise o YAML enviado, "
                    "identifique falhas e use a ferramenta 'apply_manifest' para corrigir."
                )
                prompt = f"Corrija o recurso no namespace {ns}:\n\n{live_yaml}"
                full_res = agent.run(prompt, system_instruction=sys_instruction) 

                # 4. Health Check (O veredito real do cluster)
                is_ok, msg = self.health.check_health(ns)

                # 5. Finalização (Escreve no CSV e gera o Markdown)
                self.save_results(model, yaml_file, full_res, is_ok, msg, ns)

#    def save_results(self, model, yaml_file, full_res, is_ok, health_msg, ns):
#        # Manda o Coletor escrever no CSV de 8 colunas com o veredito final
#        self.collector.commit(is_ok, health_msg)
#
#        # Salva o Markdown (opcional, mas bom para sua auditoria)
#        output_dir = f"results/{model.replace(':', '-')}"
#        verify_output = os.popen(f"kubectl get all -n {ns}").read()
#        self.save_md(output_dir, yaml_file, 1, str(full_res), "Tool Call", verify_output, is_ok, health_msg)

    def save_results(self, model, yaml_file, full_res, is_ok, health_msg, ns):
        # Manda o Coletor escrever no CSV
        self.collector.commit(is_ok, health_msg)

        output_dir = f"results/{model.replace(':', '-')}"
        verify_output = os.popen(f"kubectl get all -n {ns}").read()
        
        # Tenta pegar o código do fix se o seu AgentService retornar um objeto estruturado
        # Se full_res for apenas string, ele usa a string toda.
        fix_content = getattr(full_res, 'tool_calls', "Código não extraído") 
        
        # 1 é a repetição (ajuste se usar o loop de reps)
        self.save_md(output_dir, yaml_file, 1, str(full_res), fix_content, verify_output, is_ok, health_msg)

    def save_md(self, path, yaml, r, analysis, fix, verify, is_ok, health_msg):
        status_icon = "✅" if is_ok else "❌"
        fname = f"{path}/Teste_{yaml.split('-')[0]}.{r}_{datetime.now().strftime('%H%M%S')}.md"
        
        with open(fname, "w") as f:
            f.write(f"# Relatório: {yaml} - Rep {r}\n\n")
            f.write(f"## Status Final: {status_icon} {'SUCESSO' if is_ok else 'FALHA'}\n")
            f.write(f"**Veredito:** {health_msg}\n\n---\n\n")
            f.write(f"## 🔍 Análise\n{analysis}\n\n")
            f.write(f"## 🛠️ Fix Aplicado\n```yaml\n{fix}\n```\n\n")
            f.write(f"## 📋 Cluster Snapshot\n```\n{verify}```")

if __name__ == "__main__":
    PerformanceTestRunner().run()