import os
import time
import logging
from typing import Any, Dict, List

from src.application.services.agent_service import AgentService
from src.infrastructure.llm.openai_adapter import OpenAIAdapter
from src.infrastructure.llm.ollama_adapter import OllamaAdapter
from src.adapters.llm.metrics_decorator import LLMMonitorDecorator
from src.infrastructure.k8s_adapter.service import K8sServiceAdapter
from src.infrastructure.metrics.collector import TCCMetricsCollector
from src.infrastructure.k8s_adapter.scenario_manager import K8sScenarioManager
from src.infrastructure.k8s_adapter.health_checker import K8sHealthChecker
from src.application.services.report_exporter import ReportExporter


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("BenchmarkRunner")


class PerformanceTestRunner:
    """
    Executor dos testes de performance do AgentK.

    Configuração por variáveis de ambiente:

    PERFORMANCE_TEST_MODELS
        Lista de modelos separados por vírgula.
        Padrão: qwen2.5:3b

    PERFORMANCE_TEST_YAMLS
        Lista de cenários YAML separados por vírgula.
        Padrão: os 10 cenários de docs/tests/scenarios.

    PERFORMANCE_TEST_REPS
        Número de repetições por cenário.
        Padrão: 1 para execução local rápida.

    PERFORMANCE_TEST_SLEEP_SECONDS
        Pausa entre rodadas.
        Padrão: 5 segundos.
    """

    DEFAULT_MODELS = ["qwen2.5:3b"]

    DEFAULT_YAMLS = [
        "1-orion.yaml",
        "2-frontend.yaml",
        "3-mysql.yaml",
        "4-vllm.yaml",
        "5-nginx.yaml",
        "6-selenium.yaml",
        "7-elasticsearch.yaml",
        "8-newrelic.yaml",
        "9-storm.yaml",
        "10-mongodb.yaml",
    ]

    def __init__(self):
        self.models = self._get_csv_env(
            name="PERFORMANCE_TEST_MODELS",
            default=self.DEFAULT_MODELS,
        )

        self.yamls = self._get_csv_env(
            name="PERFORMANCE_TEST_YAMLS",
            default=self.DEFAULT_YAMLS,
        )

        self.reps = self._get_int_env(
            name="PERFORMANCE_TEST_REPS",
            default=1,
            minimum=1,
        )

        self.sleep_seconds = self._get_int_env(
            name="PERFORMANCE_TEST_SLEEP_SECONDS",
            default=5,
            minimum=0,
        )

        self.collector = TCCMetricsCollector()
        self.env_mgr = K8sScenarioManager()
        self.health = K8sHealthChecker()

        self.scenario_headers = {
            "1-orion.yaml": "Serviço: fiware-orionld-service Deployment: fiware-orion HPA: fiware-orionld-hpa",
            "2-frontend.yaml": "Deployment: frontend",
            "3-mysql.yaml": "Pod: mysql",
            "4-vllm.yaml": "Deployment: vllm-gemma-deployment",
            "5-nginx.yaml": "Service: nginxsvc; ReplicationController my-nginx",
            "6-selenium.yaml": "Deployment: selenium-hub Service: selenium-hub",
            "7-elasticsearch.yaml": "Service: elasticsearch ReplicationController: es",
            "8-newrelic.yaml": "Daemonset: newrelic-agent",
            "9-storm.yaml": "Deployment: storm-worker-controller",
            "10-mongodb.yaml": "Service: mongodb-service Deployment: mongodb-deployment",
        }

        logger.info("Configuração do benchmark carregada.")
        logger.info("Modelos: %s", self.models)
        logger.info("Cenários: %s", self.yamls)
        logger.info("Repetições por cenário: %s", self.reps)
        logger.info("Pausa entre rodadas: %s segundo(s)", self.sleep_seconds)

    def _get_csv_env(self, name: str, default: List[str]) -> List[str]:
        raw_value = os.getenv(name, "").strip()

        if not raw_value:
            return list(default)

        values = [
            item.strip()
            for item in raw_value.split(",")
            if item.strip()
        ]

        return values or list(default)

    def _get_int_env(self, name: str, default: int, minimum: int = 0) -> int:
        raw_value = os.getenv(name, "").strip()

        if not raw_value:
            return default

        try:
            value = int(raw_value)
        except ValueError:
            logger.warning(
                "Valor inválido para %s=%r. Usando padrão %s.",
                name,
                raw_value,
                default,
            )
            return default

        if value < minimum:
            logger.warning(
                "Valor abaixo do mínimo para %s=%s. Usando mínimo %s.",
                name,
                value,
                minimum,
            )
            return minimum

        return value

    def _get_agent(self, model_name: str) -> AgentService:
        """Instancia um agente novo com monitoramento de tokens/latência."""
        k8s = K8sServiceAdapter()

        if any(x in model_name for x in ["gpt", "o1", "o4"]):
            adapter = OpenAIAdapter(model=model_name)
            provider = "OpenAI"
        else:
            adapter = OllamaAdapter(model=model_name)
            provider = "Ollama"

        monitored_llm = LLMMonitorDecorator(adapter, provider, self.collector)
        return AgentService(llm_provider=monitored_llm, k8s_adapter=k8s)

    def run(self):
        logger.info("🎬 Iniciando campanha de benchmark AgentK-MCP")

        for model in self.models:
            for yaml_file in self.yamls:
                for r in range(1, self.reps + 1):
                    logger.info(
                        "🚀 [MODELO: %s] | [CENÁRIO: %s] | [RODADA: %s/%s]",
                        model,
                        yaml_file,
                        r,
                        self.reps,
                    )

                    try:
                        ns = self.env_mgr.prepare(yaml_file)

                        header = self.scenario_headers.get(yaml_file, f"Arquivo: {yaml_file}")
                        prompt = self._build_prompt(header, ns)

                        agent = self._get_agent(model)
                        full_res = agent.run(prompt)

                        is_ok, msg = self.health.check_health(ns)

                        pod_diagnostics: List[Dict[str, Any]] = []

                        if not is_ok:
                            pod_diagnostics = self._collect_failure_diagnostics(
                                agent=agent,
                                namespace=ns,
                            )

                        self._persist_results(
                            model=model,
                            yaml_name=yaml_file,
                            round_number=r,
                            response=full_res,
                            is_ok=is_ok,
                            health_msg=msg,
                            namespace=ns,
                            pod_diagnostics=pod_diagnostics,
                        )

                        time.sleep(self.sleep_seconds)

                    except Exception as exc:
                        logger.error(
                            "❌ Falha crítica no cenário %s com modelo %s na rodada %s: %s",
                            yaml_file,
                            model,
                            r,
                            exc,
                        )
                        continue

    def _build_prompt(self, header: str, ns: str) -> str:
        return (
            f"{header}\n\n"
            f"Analise os arquivos YAML dos recursos Kubernetes acima no namespace '{ns}', procurando por misconfigurations "
            f"e possíveis incoerências, considerando o deploy em ambiente de produção.\n"
            f"Utilize as ferramentas disponíveis para extrair o estado atual dos recursos.\n"
            f"Verifique se as configurações estão corretas de acordo com as especificações do Kubernetes e identifique qualquer "
            f"problema que possa comprometer a funcionalidade ou coerência com as boas práticas.\n"
            f"Para cada problema encontrado, sugira uma correção específica.\n\n"
            f"Faça a atualização do serviço e do deployment no namespace '{ns}'. Se houver conflito, remova e depois aplique.\n"
            f"Use a estratégia mais eficiente: liste recursos primeiro, busque detalhes somente dos recursos necessários, "
            f"use get_pod_diagnostics para pods Pending, ContainerCreating, FailedMount, ImagePullBackOff, ErrImagePull "
            f"ou CrashLoopBackOff, e aplique manifestos multi-documento em uma única chamada quando houver mais de um recurso.\n\n"
        )

    def _collect_failure_diagnostics(
        self,
        agent: AgentService,
        namespace: str,
    ) -> List[Dict[str, Any]]:
        """
        Coleta diagnóstico estruturado dos pods quando o HealthCheck falha.

        Isso melhora o relatório do benchmark e evita que a falha fique limitada a:
        - Timeout genérico;
        - Mensagem curta do health check;
        - kubectl get all sem causa raiz.
        """
        diagnostics: List[Dict[str, Any]] = []

        try:
            pods = agent.k8s_adapter.list_resources(
                resource_types="pods",
                namespace=namespace,
            )

            if isinstance(pods, dict):
                pods = pods.get("pods", [])

            if not isinstance(pods, list):
                return [
                    {
                        "status": "ERROR",
                        "namespace": namespace,
                        "message": f"Não foi possível listar pods para diagnóstico: {pods}",
                    }
                ]

            for pod_name in pods:
                if not pod_name:
                    continue

                diagnostic = agent.k8s_adapter.get_pod_diagnostics(
                    pod_name=pod_name,
                    namespace=namespace,
                    tail_lines=80,
                )

                diagnostics.append(diagnostic)

            return diagnostics

        except Exception as exc:
            return [
                {
                    "status": "ERROR",
                    "namespace": namespace,
                    "message": f"Erro inesperado ao coletar diagnóstico de falha: {exc}",
                }
            ]

    def _persist_results(
        self,
        model: str,
        yaml_name: str,
        round_number: int,
        response: str,
        is_ok: bool,
        health_msg: str,
        namespace: str,
        pod_diagnostics: List[Dict[str, Any]] | None = None,
    ) -> None:
        self.collector.commit(is_ok, health_msg)

        verify_output = os.popen(f"kubectl get all -n {namespace}").read()

        md_content = ReportExporter.generate_markdown(
            model=model,
            res=response,
            is_ok=is_ok,
            health_msg=health_msg,
            ns=namespace,
            verify_output=verify_output,
            yaml_name=yaml_name,
            round_num=round_number,
            pod_diagnostics=pod_diagnostics or [],
        )

        fname = ReportExporter.save_to_disk(
            model,
            yaml_name,
            round_number,
            md_content,
        )

        logger.info("💾 Resultados persistidos em: %s", fname)


if __name__ == "__main__":
    runner = PerformanceTestRunner()
    runner.run()