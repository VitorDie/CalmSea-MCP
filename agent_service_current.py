from __future__ import annotations

import hashlib
import json
import os
import re
import time
from datetime import datetime
from typing import Any, Dict, List

from src.application.interfaces.k8s_service_interface import K8sServiceInterface
from src.application.interfaces.llm_provider import LLMProviderInterface
from src.application.tools_definitions import TOOLS_SCHEMA


class AgentService:
    """
    Serviço principal do AgentK.

    Esta versão prioriza performance operacional:
    - listar recursos antes de buscar detalhes;
    - buscar detalhes somente dos recursos necessários;
    - compactar resultados grandes antes de inserir no histórico;
    - podar histórico antigo para reduzir tokens enviados ao LLM;
    - evitar reaplicar o mesmo manifesto em loop;
    - bloquear respostas finais que aleguem execução de ferramenta sem execução real;
    - encerrar cedo após apply_manifest quando o HealthCheck confirmar estabilidade;
    - evidenciar tempo gasto em chamadas à LLM e ferramentas;
    - incentivar diagnóstico por get_pod_diagnostics quando o estado não muda.
    """

    MAX_ITERATIONS = int(os.getenv("AGENTK_MAX_ITERATIONS", "20"))
    MAX_TOOL_RESULT_CHARS = int(os.getenv("AGENTK_MAX_TOOL_RESULT_CHARS", "2200"))
    MAX_LOG_CHARS = int(os.getenv("AGENTK_MAX_LOG_CHARS", "900"))
    MAX_HISTORY_MESSAGES = int(os.getenv("AGENTK_MAX_HISTORY_MESSAGES", "12"))
    MAX_BLOCKED_REPLIES = int(os.getenv("AGENTK_MAX_BLOCKED_REPLIES", "2"))
    MAX_NAMES_PER_RESOURCE_TYPE = int(os.getenv("AGENTK_MAX_NAMES_PER_RESOURCE_TYPE", "25"))
    MAX_DIAGNOSTIC_EVENTS = int(os.getenv("AGENTK_MAX_DIAGNOSTIC_EVENTS", "5"))
    MAX_DIAGNOSTIC_ISSUES = int(os.getenv("AGENTK_MAX_DIAGNOSTIC_ISSUES", "8"))

    def __init__(
        self,
        llm_provider: LLMProviderInterface,
        k8s_adapter: K8sServiceInterface,
        health_checker: Any | None = None,
        target_namespace: str | None = None,
        early_healthcheck_timeout: int | None = None,
    ):
        self.llm = llm_provider
        self.k8s_adapter = k8s_adapter
        self.health_checker = health_checker
        self.target_namespace = target_namespace
        self.early_healthcheck_timeout = (
            early_healthcheck_timeout
            if early_healthcheck_timeout is not None
            else int(os.getenv("AGENTK_EARLY_HEALTHCHECK_TIMEOUT", "25"))
        )

        # Rastreadores de estado para evitar loops e respostas fabricadas.
        self._last_obs_hash = None
        self._last_manifest_hash = None
        self._repeated_manifest_count = 0
        self._last_tool_name = None
        self._last_tool_result = None
        self._last_apply_success = False
        self._last_tool_error = None
        self._blocked_reply_count = 0
        self._executed_tool_names = []
        self._executed_iterations = 0
        self._last_health_after_apply = None

        self.system_instruction = (
            "Você é AgentK, especialista em diagnóstico, correção e otimização de recursos YAML do Kubernetes.\n"
            "Seu objetivo é estabilizar o ambiente com o menor número possível de iterações, chamadas de ferramenta e tokens.\n\n"

            "Estratégia obrigatória de performance:\n"
            "1. Primeiro use list_resources para listar nomes de recursos de forma enxuta.\n"
            "2. Sempre que possível, liste múltiplos tipos em uma única chamada, por exemplo: "
            "['pods', 'services', 'deployments', 'configmaps', 'secrets', 'ingresses'].\n"
            "3. Só use get_resource_details depois de identificar, pela listagem, quais recursos realmente precisam de análise.\n"
            "4. Nunca chame get_resource_details sem informar resource_type, name e namespace.\n"
            "5. Não busque detalhes completos de todos os recursos se apenas um pod, service ou deployment parece problemático.\n"
            "6. Se um pod estiver em CrashLoopBackOff, Error, ImagePullBackOff, ErrImagePull, ContainerCreating por muito tempo "
            "ou não estabilizar após apply, use get_pod_diagnostics antes de reaplicar outro manifesto. "
            "Use get_pod_logs depois apenas se o diagnóstico indicar falha da aplicação ou se o container já tiver iniciado.\n"
            "7. Ao aplicar correções, gere um manifesto limpo, sem uid, resourceVersion, managedFields, creationTimestamp, "
            "generation, selfLink, ownerReferences, finalizers ou status.\n"
            "8. Quando precisar aplicar vários recursos, use um único YAML multi-documento separado por '---' e chame apply_manifest uma vez.\n"
            "9. Não aplique o mesmo manifesto repetidamente. Se o estado não mudou, investigue o diagnóstico do pod, eventos e detalhes específicos.\n"
            "10. Evite alterar recursos de sistema ou namespaces kube-system, kube-public e kube-node-lease, salvo quando o usuário "
            "pedir explicitamente leitura ou diagnóstico desses namespaces.\n"
            "11. Nunca diga que executou uma ferramenta, aplicou manifesto ou corrigiu o cluster sem ter recebido o resultado real "
            "da ferramenta correspondente.\n"
            "12. Nunca use placeholders ou valores fictícios em manifestos aplicados. São proibidos valores como "
            "BASE64_CERT_HERE, BASE64_KEY_HERE, <CERT PEM CONTENT>, <KEY PEM CONTENT>, <COLE...>, '...', TODO ou textos de instrução.\n"
            "13. Se não houver certificado TLS real, não crie Secret kubernetes.io/tls fictício. Em vez disso, simplifique o manifesto "
            "para HTTP, remova mounts/configurações de TLS que exigem certificado real, ou explique que não é possível aplicar TLS sem dados reais.\n"
            "14. Não invente tags de imagem. Se uma imagem/tag falhar com ErrImagePull, use uma imagem oficial e existente apenas quando "
            "a configuração também for compatível com essa imagem. Exemplo: se trocar para nginx oficial, remova scripts customizados "
            "como /home/auto-reload-nginx.sh que não existem nessa imagem.\n"
            "15. Se apply_manifest retornar sucesso e o HealthCheck informar estabilidade, finalize. Não continue chamando ferramentas.\n"
            "16. Mantenha respostas finais objetivas. Não repita YAML completo se ele já foi aplicado com sucesso, a menos que seja necessário.\n\n"

            "Capacidades disponíveis:\n"
            "- Listar recursos Kubernetes de forma enxuta.\n"
            "- Obter detalhes limpos de recursos específicos.\n"
            "- Diagnosticar pods com get_pod_diagnostics, incluindo events, FailedMount, Secret ausente, ConfigMap ausente, "
            "ImagePullBackOff, ErrImagePull, CrashLoopBackOff e command/entrypoint inexistente.\n"
            "- Ler logs de pods.\n"
            "- Aplicar manifestos com validação de placeholders e dry-run server-side antes do apply real.\n"
            "- Remover recursos específicos quando necessário.\n"
            "- Escalar deployments, statefulsets e replication_controllers.\n\n"

            "Recursos suportados e apiVersion correta:\n"
            "- Pod: apiVersion v1.\n"
            "- Service: apiVersion v1.\n"
            "- ConfigMap: apiVersion v1.\n"
            "- Secret: apiVersion v1.\n"
            "- PersistentVolumeClaim: apiVersion v1.\n"
            "- ReplicationController: apiVersion v1. Nunca use apps/v1 para ReplicationController. "
            "ReplicationController é recurso nativo antigo do Kubernetes, não é CRD.\n"
            "- Deployment: apiVersion apps/v1.\n"
            "- ReplicaSet: apiVersion apps/v1.\n"
            "- StatefulSet: apiVersion apps/v1.\n"
            "- DaemonSet: apiVersion apps/v1.\n"
            "- Ingress: apiVersion networking.k8s.io/v1.\n"
            "- Job: apiVersion batch/v1.\n"
            "- CronJob: apiVersion batch/v1.\n"
            "- HorizontalPodAutoscaler: apiVersion autoscaling/v2.\n"
            "- Namespace: apiVersion v1.\n"
            "- Node: apiVersion v1.\n"
            "- PersistentVolume: apiVersion v1.\n\n"

            "Regra específica para ReplicationController:\n"
            "- Se o recurso existente for ReplicationController, preserve kind: ReplicationController e use apiVersion: v1, "
            "a menos que a migração para Deployment seja explicitamente necessária.\n"
            "- Se migrar de ReplicationController para Deployment, remova ou neutralize o ReplicationController antigo, "
            "caso contrário o pod antigo continuará existindo e o HealthCheck poderá falhar.\n"
            "- Não invente que ReplicationController exige CRD. Ele é recurso nativo do Kubernetes.\n\n"

            "Regras específicas para Nginx e pods com volume:\n"
            "- Se get_pod_diagnostics indicar missing_secret ou missing_configmap, corrija criando o recurso ausente com dados válidos "
            "ou removendo a referência de volume. Não crie Secret/ConfigMap com placeholders.\n"
            "- Se get_pod_diagnostics indicar container_command_not_found, remova ou corrija command/args. "
            "Para imagem oficial nginx, normalmente não declare command customizado.\n"
            "- Se get_pod_diagnostics indicar image_pull_error, ErrImagePull ou ImagePullBackOff, corrija imagem/tag para uma existente. "
            "Depois revise command, probes, mounts e config para compatibilidade com a nova imagem.\n"
            "- Se usar nginx oficial, prefira uma configuração HTTP simples e válida. Não configure SSL/TLS sem certificado e chave reais.\n\n"

            "Regras específicas para falhas recorrentes:\n"
            "- MySQL: se logs indicarem unknown option '--ignore-db-dir', remova esse argumento. "
            "Se o erro mencionar couldn't find key em Secret, corrija a chave ausente no Secret ou remova a referência.\n"
            "- MySQL em Pod standalone: se get_resource_details mostrar kind Pod com imagem my-sql, argumento --ignore-db-dir "
            "ou volume cloud incompatível com Minikube, não tente aplicar outro Pod por cima. Pods têm spec praticamente imutável. "
            "A próxima ação eficiente é remover o Pod antigo com delete_resource e aplicar um Deployment apps/v1 com Service, "
            "imagem mysql oficial existente e volume compatível com Minikube, como emptyDir para benchmark.\n"
            "- NewRelic: se logs indicarem no license key, configure NRIA_LICENSE_KEY com Secret real ou explique que não é possível estabilizar sem licença.\n"
            "- Elasticsearch: se PVC ficar sem binding, use storage compatível com Minikube para benchmark, como hostPath/PV manual ou emptyDir quando aceitável.\n"
            "- Storm/Orion: se a tag de imagem falhar com manifest unknown, não tente variações inventadas; use imagem já existente ou tag comprovadamente funcional.\n\n"

            "Boas práticas esperadas:\n"
            "- Usar imagens com tags explícitas e estáveis, mas apenas tags existentes.\n"
            "- Corrigir selectors e labels inconsistentes.\n"
            "- Evitar credenciais expostas em texto claro quando possível.\n"
            "- Definir requests e limits quando fizer sentido.\n"
            "- Usar volumes compatíveis com Minikube, como emptyDir, configMap, secret válido ou hostPath, evitando drivers cloud.\n"
            "- Manter YAML simples, válido, limpo e aplicável.\n"
            "- Não aplicar YAML com valores de exemplo, comentários instrutivos como dados, placeholders, certificados falsos ou base64 inválido.\n\n"

            "Formato de resposta:\n"
            "- Explique de forma objetiva o diagnóstico.\n"
            "- Mostre a correção aplicada ou recomendada.\n"
            "- Informe o estado esperado após a correção.\n"
            "- Se não conseguir estabilizar, diga claramente o motivo técnico provável.\n"
            "- Não declare execução de ferramenta se a ferramenta não tiver sido chamada de fato."
        )

    def run(self, user_prompt: str, system_instruction: str = None) -> str:
        history: List[Dict[str, str]] = []
        self._append_history(history, "user", user_prompt, prune=False)

        base_instruction = system_instruction or self.system_instruction
        run_started_at = time.perf_counter()

        print(
            f"[TIME][{self._now()}] AgentService.run iniciado. "
            f"Prompt inicial com {len(user_prompt)} caracteres.",
            flush=True,
        )

        for iteration in range(self.MAX_ITERATIONS):
            self._executed_iterations = iteration + 1
            iteration_started_at = time.perf_counter()
            tentativas_restantes = self.MAX_ITERATIONS - iteration

            aviso_urgencia = (
                f"\n[SISTEMA]: Tentativa {iteration + 1}/{self.MAX_ITERATIONS}. "
                f"{tentativas_restantes} tentativa(s) restante(s).\n"
                "Regra de eficiência: liste recursos antes de buscar detalhes. "
                "Se o estado não mudar, não reaplique o mesmo YAML; consulte get_pod_diagnostics, eventos e detalhes específicos. "
                "Não use placeholders, certificados fictícios, base64 inválido ou tags inventadas. "
                "Não finalize alegando execução de ferramenta sem resultado real. "
                "Se HealthCheck pós-apply já confirmou sucesso, finalize sem nova investigação."
            )

            print(
                f"\n[TIME][{self._now()}] >>> Iniciando iteração {iteration}/{self.MAX_ITERATIONS - 1}. "
                f"Mensagens no histórico: {len(history)}.",
                flush=True,
            )

            llm_started_at = time.perf_counter()
            print(
                f"[TIME][{self._now()}] >>> Chamando LLM.decide_tool na iteração {iteration}. "
                "Se o processo ficar parado após esta linha, a espera está na resposta do modelo/Ollama.",
                flush=True,
            )

            decision = self.llm.decide_tool(
                messages=history,
                tools_schema=TOOLS_SCHEMA,
                system_instruction=base_instruction + aviso_urgencia,
            )

            llm_elapsed = time.perf_counter() - llm_started_at
            print(
                f"[TIME][{self._now()}] <<< LLM.decide_tool respondeu na iteração {iteration}. "
                f"Duração: {llm_elapsed:.2f}s.",
                flush=True,
            )

            print(f"\n--- ITERAÇÃO {iteration} ---", flush=True)
            print(f"Decisão da IA: {decision}", flush=True)

            action = decision.get("action")

            if action == "reply":
                reply_content = decision.get("content", "")

                print(
                    f"[TIME][{self._now()}] Reply recebido na iteração {iteration}. "
                    f"Tamanho: {len(reply_content)} caracteres.",
                    flush=True,
                )

                reply_validation_error = self._validate_reply_before_return(reply_content)

                if reply_validation_error:
                    self._blocked_reply_count += 1

                    print(
                        "[WATCHDOG] Resposta final bloqueada "
                        f"({self._blocked_reply_count}/{self.MAX_BLOCKED_REPLIES}): "
                        f"{reply_validation_error}",
                        flush=True,
                    )

                    if self._blocked_reply_count >= self.MAX_BLOCKED_REPLIES:
                        total_elapsed = time.perf_counter() - run_started_at

                        return (
                            "⚠️ Execução interrompida pelo watchdog: o modelo tentou finalizar a resposta "
                            "alegando execução de ferramenta sem uma chamada real correspondente. "
                            "O cluster não deve ser considerado corrigido. "
                            f"Tempo total até interrupção: {total_elapsed:.2f}s. "
                            f"Última orientação do sistema: {reply_validation_error}"
                        )

                    self._append_history(history, "user", reply_validation_error)

                    print(
                        f"[TIME][{self._now()}] Resposta bloqueada reinserida no histórico. "
                        "Indo para a próxima iteração.",
                        flush=True,
                    )
                    continue

                total_elapsed = time.perf_counter() - run_started_at
                print(
                    f"[TIME][{self._now()}] AgentService.run finalizado por reply válida. "
                    f"Tempo total: {total_elapsed:.2f}s.",
                    flush=True,
                )

                return reply_content

            if action == "error":
                total_elapsed = time.perf_counter() - run_started_at
                print(
                    f"[TIME][{self._now()}] AgentService.run finalizado por action=error. "
                    f"Tempo total: {total_elapsed:.2f}s.",
                    flush=True,
                )
                return f"❌ Erro de Contexto: {decision.get('content')}"

            tool_calls = self._extract_tool_calls(decision)

            if not tool_calls:
                self._append_history(
                    history,
                    "user",
                    (
                        "[SISTEMA]: Nenhuma ferramenta válida foi selecionada. "
                        "Responda ao usuário ou escolha uma ferramenta válida."
                    ),
                )

                print(
                    f"[TIME][{self._now()}] Nenhuma ferramenta válida selecionada. "
                    f"Duração da iteração {iteration}: {time.perf_counter() - iteration_started_at:.2f}s.",
                    flush=True,
                )
                continue

            print(
                f"[TIME][{self._now()}] Total de ferramentas na iteração {iteration}: {len(tool_calls)}.",
                flush=True,
            )

            early_stop_response = ""

            for call_index, call in enumerate(tool_calls, start=1):
                tool_name = call.get("tool_name")
                args = call.get("tool_args", {}) or {}

                tool_started_at = time.perf_counter()

                print(
                    f"[TIME][{self._now()}] >>> Executando ferramenta {call_index}/{len(tool_calls)}: "
                    f"{tool_name} com args={self._compact_args_for_log(args)}",
                    flush=True,
                )

                try:
                    result = self._execute_tool(tool_name, args)

                    tool_elapsed = time.perf_counter() - tool_started_at

                    print(
                        f"[TIME][{self._now()}] <<< Ferramenta {tool_name} finalizada. "
                        f"Duração: {tool_elapsed:.2f}s.",
                        flush=True,
                    )

                    self._blocked_reply_count = 0
                    self._last_tool_name = tool_name
                    self._last_tool_result = result

                    if tool_name:
                        self._executed_tool_names.append(tool_name)

                    tool_error = self._detect_tool_error(
                        tool_name=tool_name,
                        args=args,
                        result=result,
                    )

                    self._last_tool_error = tool_error

                    if tool_name == "apply_manifest":
                        self._last_apply_success = (
                            isinstance(result, dict)
                            and str(result.get("status", "")).upper() == "SUCCESS"
                        )

                    print(
                        f"[DEBUG] Resultado compacto da {tool_name}: "
                        f"{self._compact_tool_result(tool_name, result)}",
                        flush=True,
                    )

                    msg = self._build_watchdog_message(
                        tool_name=tool_name,
                        args=args,
                        result=result,
                    )

                    if tool_name == "apply_manifest" and self._last_apply_success:
                        health_msg = self._run_early_healthcheck()

                        if health_msg:
                            msg = f"{msg}\n\n{health_msg}"

                            if health_msg.startswith("[SISTEMA]: HealthCheck pós-apply confirmou sucesso"):
                                early_stop_response = self._build_early_success_response(
                                    health_msg=health_msg,
                                    tool_result=result,
                                )

                    compact_result = self._compact_tool_result(
                        tool_name=tool_name,
                        result=result,
                    )

                    self._append_history(
                        history,
                        "assistant",
                        f"Executei: {tool_name}",
                    )

                    self._append_history(
                        history,
                        "user",
                        (
                            f"[SISTEMA]: Resultado compacto de {tool_name}:\n"
                            f"{compact_result}\n\n"
                            f"{msg}"
                        ),
                    )

                    if early_stop_response:
                        total_elapsed = time.perf_counter() - run_started_at
                        print(
                            f"[TIME][{self._now()}] AgentService.run finalizado por early-stop pós-apply. "
                            f"Tempo total: {total_elapsed:.2f}s.",
                            flush=True,
                        )
                        return early_stop_response

                except Exception as exc:
                    tool_elapsed = time.perf_counter() - tool_started_at

                    print(
                        f"[TIME][{self._now()}] <<< Ferramenta {tool_name} falhou. "
                        f"Duração: {tool_elapsed:.2f}s. Erro: {exc}",
                        flush=True,
                    )

                    self._last_tool_error = {
                        "tool_name": tool_name,
                        "args": args,
                        "error": str(exc),
                    }

                    self._append_history(
                        history,
                        "user",
                        (
                            f"[ERRO TÉCNICO em {tool_name}]: {str(exc)}. "
                            "Corrija os argumentos da ferramenta antes de prosseguir."
                        ),
                    )

            iteration_elapsed = time.perf_counter() - iteration_started_at

            print(
                f"[TIME][{self._now()}] <<< Iteração {iteration} finalizada. "
                f"Duração total da iteração: {iteration_elapsed:.2f}s. "
                f"Histórico atual: {len(history)} mensagens.",
                flush=True,
            )

        total_elapsed = time.perf_counter() - run_started_at

        print(
            f"[TIME][{self._now()}] AgentService.run finalizado por limite de iterações. "
            f"Tempo total: {total_elapsed:.2f}s.",
            flush=True,
        )

        return (
            "⚠️ Limite de iterações atingido: o AgentK não conseguiu estabilizar o cluster "
            "dentro do número máximo de tentativas."
        )

    def _extract_tool_calls(self, decision: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Normaliza a decisão da LLM em uma lista de chamadas de ferramenta.

        Mantém compatibilidade com:
        - action == parallel_tool_use;
        - action com uma única ferramenta.
        """
        if decision.get("action") == "parallel_tool_use":
            calls = decision.get("calls", [])

            if isinstance(calls, list):
                return calls

            return []

        tool_name = decision.get("tool_name")

        if not tool_name:
            return []

        return [{
            "tool_name": tool_name,
            "tool_args": decision.get("tool_args", {}) or {},
        }]

    def _detect_tool_error(
        self,
        tool_name: str,
        args: Dict[str, Any],
        result: Any,
    ) -> Dict[str, Any] | None:
        """
        Identifica erros retornados por ferramentas sem depender apenas de exceções.
        """
        if isinstance(result, dict):
            status = str(result.get("status", "")).upper()
            valid = result.get("valid")

            if status == "ERROR" or valid is False or "error" in result:
                return {
                    "tool_name": tool_name,
                    "args": args,
                    "error": result.get("message") or result.get("error") or str(result),
                }

        if isinstance(result, list):
            for item in result:
                if isinstance(item, str) and item.lower().startswith("erro"):
                    return {
                        "tool_name": tool_name,
                        "args": args,
                        "error": item,
                    }

        return None

    def _build_watchdog_message(
        self,
        tool_name: str,
        args: Dict[str, Any],
        result: Any,
    ) -> str:
        """
        Gera mensagens de controle para evitar loops e orientar o próximo passo.
        """
        result_text = str(result)
        result_text_lower = result_text.lower()
        msg = "Ação aceita."

        if tool_name == "list_resources":
            msg = (
                "Próximo passo recomendado: selecione apenas os recursos suspeitos "
                "e use get_resource_details neles. Evite buscar detalhes de tudo."
            )

        elif tool_name == "get_resource_details":
            obs_signature = self._hash_payload(result)
            pod_fastpath_msg = self._build_pod_detail_fastpath_message(result)

            if pod_fastpath_msg:
                msg = pod_fastpath_msg
            elif obs_signature == self._last_obs_hash:
                msg = (
                    "SISTEMA: Estagnação detectada. O estado observado não mudou. "
                    "Use get_pod_diagnostics se houver pod instável ou revise o manifesto antes de reaplicar."
                )
            else:
                msg = (
                    "Detalhes obtidos. Se houver erro em pod, service, selector, secret, image ou volume, "
                    "corrija somente o necessário."
                )

            self._last_obs_hash = obs_signature

        elif tool_name == "get_pod_diagnostics":
            detected_issue_types = self._extract_detected_issue_types(result)
            logs_text = ""

            if isinstance(result, dict):
                logs_text = str(result.get("logs_tail", "") or "").lower()

            if "container_command_not_found" in detected_issue_types:
                msg = (
                    "Diagnóstico estruturado do pod obtido. Causa prioritária: command/entrypoint inexistente. "
                    "Remova ou corrija command/args antes de reaplicar. Se estiver usando imagem oficial, "
                    "não referencie script customizado que não existe dentro da imagem."
                )
            elif detected_issue_types.intersection({"image_pull_error", "image_pull_backoff", "err_image_pull"}):
                msg = (
                    "Diagnóstico estruturado do pod obtido. Causa prioritária: falha de pull de imagem. "
                    "Corrija imagem/tag para uma existente e não invente tags. Após trocar a imagem, "
                    "garanta que command, probes, env e volumes sejam compatíveis com a nova imagem."
                )
            elif detected_issue_types.intersection({"missing_secret", "missing_configmap", "failed_mount"}):
                msg = (
                    "Diagnóstico estruturado do pod obtido. Causa prioritária: FailedMount por Secret/ConfigMap ausente. "
                    "Crie recursos ausentes com valores reais válidos ou remova as referências de volume. "
                    "Não use placeholders, certificados fictícios, base64 inválido ou textos como <CERT PEM CONTENT>."
                )
            elif detected_issue_types.intersection({"create_container_config_error"}):
                msg = (
                    "Diagnóstico estruturado do pod obtido. Causa prioritária: erro de configuração do container. "
                    "Verifique Secret/ConfigMap referenciados por env, envFrom, volumeMounts e chaves ausentes. "
                    "Se a mensagem citar couldn't find key, corrija o Secret antes de reaplicar."
                )
            elif "unknown option '--ignore-db-dir'" in logs_text:
                msg = (
                    "Diagnóstico estruturado do pod obtido. Logs indicam que MySQL não aceita '--ignore-db-dir'. "
                    "Remova esse argumento do container antes de reaplicar."
                )
            elif "no license key" in logs_text or "nria_license_key" in logs_text:
                msg = (
                    "Diagnóstico estruturado do pod obtido. Logs indicam ausência de licença New Relic. "
                    "Configure NRIA_LICENSE_KEY por Secret real ou explique que não é possível estabilizar o agente sem licença."
                )
            else:
                msg = (
                    "Diagnóstico estruturado do pod obtido. Use detected_issues, probable_root_cause "
                    "e recommended_actions para corrigir a causa raiz antes de reaplicar manifesto."
                )

        elif tool_name == "get_pod_logs":
            logs_lower = result_text_lower

            if "unknown option '--ignore-db-dir'" in logs_lower:
                msg = (
                    "Logs obtidos. Causa provável: argumento inválido do MySQL. "
                    "Remova '--ignore-db-dir' e reaplique somente o Deployment corrigido."
                )
            elif "no license key" in logs_lower:
                msg = (
                    "Logs obtidos. Causa provável: licença New Relic ausente. "
                    "Configure NRIA_LICENSE_KEY via Secret real ou informe que a estabilização depende desse valor."
                )
            else:
                msg = (
                    "Logs obtidos. Use essas evidências para corrigir a causa raiz. "
                    "Não reaplique YAML sem incorporar o diagnóstico dos logs."
                )

        elif tool_name == "apply_manifest":
            manifest_hash = self._hash_manifest(args.get("manifest", ""))

            if (
                "no matches for kind" in result_text_lower
                and "replicationcontroller" in result_text_lower
                and "apps/v1" in result_text_lower
            ):
                msg = (
                    "SISTEMA: O dry-run falhou porque ReplicationController foi usado com apiVersion apps/v1. "
                    "Isso está incorreto. ReplicationController é recurso nativo do Kubernetes em apiVersion v1, "
                    "não é CRD. Corrija o manifesto para apiVersion: v1 e chame apply_manifest novamente. "
                    "Não responda ao usuário antes de tentar a correção."
                )

            elif "placeholder" in result_text_lower or "valores fictícios" in result_text_lower:
                msg = (
                    "SISTEMA: O manifesto foi bloqueado porque contém placeholders ou valores fictícios. "
                    "Não reaplique com BASE64_CERT_HERE, BASE64_KEY_HERE, <CERT PEM CONTENT>, '...' ou textos instrutivos. "
                    "Substitua por valores reais válidos ou remova o recurso/campo que depende desses valores."
                )

            elif "illegal base64 data" in result_text_lower:
                msg = (
                    "SISTEMA: O dry-run falhou por base64 inválido. "
                    "Não use BASE64_CERT_HERE, BASE64_KEY_HERE ou textos de exemplo em data. "
                    "Use stringData com valor real quando apropriado ou remova o Secret TLS se não houver certificado real."
                )

            elif "field is immutable" in result_text_lower and "secret" in result_text_lower:
                msg = (
                    "SISTEMA: O dry-run falhou porque o tipo/campo imutável de um Secret existente mudou. "
                    "Remova o Secret antigo com delete_resource somente se for seguro e necessário, ou mantenha o tipo atual. "
                    "Não tente transformar Secret Opaque em kubernetes.io/tls com placeholder."
                )

            elif "dry-run falhou" in result_text_lower or "dry-run failed" in result_text_lower:
                msg = (
                    "SISTEMA: O dry-run falhou e o manifesto não foi aplicado. "
                    "Analise a mensagem de erro, corrija o YAML e chame apply_manifest novamente. "
                    "Não trate uma falha de dry-run como correção concluída."
                )

            elif manifest_hash == self._last_manifest_hash:
                self._repeated_manifest_count += 1
                msg = (
                    "SISTEMA: Manifesto idêntico ou praticamente igual já foi aplicado. "
                    "Não reaplique em loop. Se o ambiente ainda não estabilizou, "
                    "use get_pod_diagnostics no pod não pronto ou corrija apenas o campo responsável pela falha."
                )

            else:
                self._repeated_manifest_count = 0
                msg = (
                    "Manifesto enviado ao adapter. O adapter executa dry-run server-side antes do apply real. "
                    "Agora verifique o estado com list_resources e detalhes apenas dos recursos afetados."
                )

            self._last_manifest_hash = manifest_hash

        should_preserve_apply_manifest_guidance = (
            tool_name == "apply_manifest"
            and (
                "dry-run falhou" in result_text_lower
                or "dry-run failed" in result_text_lower
                or "no matches for kind" in result_text_lower
                or "placeholder" in result_text_lower
                or "valores fictícios" in result_text_lower
            )
        )

        if (
            "ERROR" in result_text
            or "Erro" in result_text
            or "erro" in result_text
            or "falhou" in result_text_lower
        ) and not should_preserve_apply_manifest_guidance:
            msg = (
                "BLOQUEIO: O comando indicou falha. Analise o erro antes de prosseguir. "
                f"Resultado: {self._truncate(result_text, 900)}"
            )

        return msg

    def _build_pod_detail_fastpath_message(self, result: Any) -> str:
        """
        Gera orientação determinística quando get_resource_details mostra um Pod
        standalone com problemas previsíveis.

        Exemplo real: 3-mysql.yaml vinha como Pod/mysql com imagem "my-sql",
        argumento "--ignore-db-dir" e volume cloud incompatível. Tentar aplicar
        outro Pod sobre esse objeto gera erro de spec imutável e consome uma
        iteração longa. A orientação mais eficiente é remover o Pod antigo e
        aplicar um Deployment + Service.
        """
        if not isinstance(result, dict):
            return ""

        kind = str(result.get("kind", "") or "").lower()

        if kind != "pod":
            return ""

        metadata = result.get("metadata", {}) or {}
        spec = result.get("spec", {}) or {}

        pod_name = metadata.get("name") or "<nome-do-pod>"
        namespace = metadata.get("namespace") or "<namespace>"

        containers = spec.get("containers", []) or []
        volumes = spec.get("volumes", []) or []

        images: List[str] = []
        args_values: List[str] = []

        for container in containers:
            if not isinstance(container, dict):
                continue

            image = str(container.get("image", "") or "")
            images.append(image)

            args = container.get("args", []) or []

            if isinstance(args, list):
                args_values.extend(str(arg) for arg in args)
            elif args:
                args_values.append(str(args))

        unsupported_volume_keys = {
            "cinder",
            "awsElasticBlockStore",
            "gcePersistentDisk",
            "azureDisk",
            "azureFile",
            "vsphereVolume",
            "rbd",
            "cephfs",
            "glusterfs",
            "iscsi",
            "nfs",
            "scaleIO",
            "portworxVolume",
            "quobyte",
            "flexVolume",
            "flocker",
        }

        unsupported_volumes = []

        for volume in volumes:
            if not isinstance(volume, dict):
                continue

            for volume_key in unsupported_volume_keys:
                if volume.get(volume_key) is not None:
                    unsupported_volumes.append({
                        "name": volume.get("name"),
                        "type": volume_key,
                    })

        has_known_mysql_bad_image = any(image in {"my-sql", "mysql"} for image in images)
        has_ignore_db_dir = any("--ignore-db-dir" in arg for arg in args_values)
        has_unsupported_volume = bool(unsupported_volumes)

        if not (has_known_mysql_bad_image or has_ignore_db_dir or has_unsupported_volume):
            return ""

        detected = []

        if has_known_mysql_bad_image:
            detected.append(f"imagem suspeita/inadequada: {', '.join(images)}")

        if has_ignore_db_dir:
            detected.append("argumento incompatível com MySQL 8: --ignore-db-dir")

        if has_unsupported_volume:
            volume_summary = ", ".join(
                f"{item.get('name')}:{item.get('type')}"
                for item in unsupported_volumes
            )
            detected.append(f"volume incompatível ou indesejado para Minikube: {volume_summary}")

        detected_text = "; ".join(detected)

        return (
            "SISTEMA: get_resource_details identificou um Pod standalone problemático. "
            f"Recurso: Pod/{pod_name} no namespace {namespace}. "
            f"Achados: {detected_text}. "
            "Não tente aplicar outro kind: Pod por cima, porque Pods têm spec praticamente imutável "
            "e isso tende a gerar immutable_pod_update. Próxima ação recomendada: chame delete_resource "
            f"com resource_type='pods', name='{pod_name}' e namespace='{namespace}'. Depois aplique um YAML "
            "multi-documento com Service v1 e Deployment apps/v1, usando imagem oficial existente e configuração "
            "compatível com Minikube. Para benchmark local, use emptyDir se não houver PVC/PV válido."
        )


    def _compact_tool_result(self, tool_name: str, result: Any) -> str:
        """
        Reduz o tamanho do resultado inserido no histórico.

        O relatório final pode manter diagnósticos completos, mas o LLM deve receber
        somente o necessário para decidir o próximo passo.
        """
        if tool_name == "list_resources" and isinstance(result, dict):
            return self._safe_json_dumps(self._compact_list_resources(result))

        if tool_name == "get_pod_diagnostics" and isinstance(result, dict):
            return self._safe_json_dumps(self._compact_pod_diagnostics(result))

        if tool_name == "get_pod_logs" and isinstance(result, str):
            return self._truncate(result, self.MAX_LOG_CHARS)

        if tool_name == "get_resource_details" and isinstance(result, dict):
            return self._safe_json_dumps(self._compact_k8s_object(result))

        if tool_name == "apply_manifest" and isinstance(result, dict):
            compact = {
                "status": result.get("status"),
                "message": self._truncate(str(result.get("message", "")), 1200),
            }
            return self._safe_json_dumps(compact)

        if isinstance(result, (dict, list)):
            return self._truncate(
                self._safe_json_dumps(result),
                self.MAX_TOOL_RESULT_CHARS,
            )

        return self._truncate(str(result), self.MAX_TOOL_RESULT_CHARS)

    def _compact_list_resources(self, result: Dict[str, Any]) -> Dict[str, Any]:
        compact = {}

        for resource_type, names in result.items():
            if isinstance(names, list):
                compact[resource_type] = {
                    "count": len(names),
                    "names": names[: self.MAX_NAMES_PER_RESOURCE_TYPE],
                }

                if len(names) > self.MAX_NAMES_PER_RESOURCE_TYPE:
                    compact[resource_type]["truncated"] = True
                    compact[resource_type]["omitted"] = len(names) - self.MAX_NAMES_PER_RESOURCE_TYPE
            else:
                compact[resource_type] = names

        return compact

    def _compact_pod_diagnostics(self, result: Dict[str, Any]) -> Dict[str, Any]:
        events = result.get("events", []) or []
        warning_events = [
            event
            for event in events
            if str(event.get("type", "")).lower() == "warning"
        ]

        compact_events = []

        for event in warning_events[: self.MAX_DIAGNOSTIC_EVENTS]:
            compact_events.append({
                "reason": event.get("reason"),
                "message": self._truncate(str(event.get("message", "")), 350),
                "count": event.get("count"),
                "last_timestamp": event.get("last_timestamp"),
            })

        detected_issues = result.get("detected_issues", []) or []

        compact_issues = []

        for issue in detected_issues[: self.MAX_DIAGNOSTIC_ISSUES]:
            if not isinstance(issue, dict):
                continue

            compact_issues.append({
                "type": issue.get("type"),
                "name": issue.get("name"),
                "severity": issue.get("severity"),
                "message": self._truncate(str(issue.get("message", "")), 450),
                "source": issue.get("source"),
            })

        container_states = result.get("container_states", []) or []

        compact_container_states = []

        for container_state in container_states[:5]:
            if not isinstance(container_state, dict):
                continue

            compact_container_states.append({
                "container": container_state.get("container"),
                "ready": container_state.get("ready"),
                "restart_count": container_state.get("restart_count"),
                "state": container_state.get("state"),
                "reason": container_state.get("reason"),
                "message": self._truncate(str(container_state.get("message", "")), 350),
                "exit_code": container_state.get("exit_code"),
            })

        return {
            "status": result.get("status"),
            "pod_name": result.get("pod_name"),
            "namespace": result.get("namespace"),
            "phase": result.get("phase"),
            "probable_root_cause": result.get("probable_root_cause"),
            "detected_issues": compact_issues,
            "container_states": compact_container_states,
            "recommended_actions": result.get("recommended_actions", [])[:5],
            "warning_events": compact_events,
            "logs_tail": self._truncate(str(result.get("logs_tail", "") or ""), self.MAX_LOG_CHARS),
        }

    def _compact_k8s_object(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        metadata = obj.get("metadata", {}) or {}
        spec = obj.get("spec", {}) or {}
        status = obj.get("status", {}) or {}

        compact: Dict[str, Any] = {
            "apiVersion": obj.get("apiVersion"),
            "kind": obj.get("kind"),
            "metadata": {
                "name": metadata.get("name"),
                "namespace": metadata.get("namespace"),
                "labels": metadata.get("labels"),
            },
        }

        kind = str(obj.get("kind", "")).lower()

        if kind in {"deployment", "statefulset", "daemonset", "replicationcontroller", "replicaset"}:
            compact["spec"] = self._compact_workload_spec(spec)

        elif kind == "pod":
            compact["spec"] = self._compact_pod_spec(spec)
            compact["status"] = self._compact_pod_status(status)

        elif kind == "service":
            compact["spec"] = {
                "type": spec.get("type"),
                "selector": spec.get("selector"),
                "ports": spec.get("ports"),
            }

        elif kind == "secret":
            data = spec.get("data") or obj.get("data") or {}
            string_data = spec.get("stringData") or obj.get("stringData") or {}

            compact["type"] = obj.get("type")
            compact["data_keys"] = sorted(list(data.keys())) if isinstance(data, dict) else []
            compact["stringData_keys"] = sorted(list(string_data.keys())) if isinstance(string_data, dict) else []

        elif kind == "configmap":
            data = obj.get("data") or {}
            compact["data_keys"] = sorted(list(data.keys())) if isinstance(data, dict) else []

        elif kind in {"persistentvolumeclaim", "persistentvolume"}:
            compact["spec"] = {
                "accessModes": spec.get("accessModes"),
                "storageClassName": spec.get("storageClassName"),
                "resources": spec.get("resources"),
                "capacity": spec.get("capacity"),
                "hostPath": spec.get("hostPath"),
            }
            compact["status"] = {
                "phase": status.get("phase"),
                "capacity": status.get("capacity"),
            }

        elif kind == "horizontalpodautoscaler":
            compact["spec"] = {
                "scaleTargetRef": spec.get("scaleTargetRef"),
                "minReplicas": spec.get("minReplicas"),
                "maxReplicas": spec.get("maxReplicas"),
                "metrics": spec.get("metrics"),
            }
            compact["status"] = {
                "currentReplicas": status.get("currentReplicas"),
                "desiredReplicas": status.get("desiredReplicas"),
                "conditions": status.get("conditions"),
            }

        else:
            compact["spec_keys"] = sorted(list(spec.keys())) if isinstance(spec, dict) else []
            compact["status_keys"] = sorted(list(status.keys())) if isinstance(status, dict) else []

        return compact

    def _compact_workload_spec(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        template = spec.get("template", {}) or {}
        template_metadata = template.get("metadata", {}) or {}
        template_spec = template.get("spec", {}) or {}

        return {
            "replicas": spec.get("replicas"),
            "selector": spec.get("selector"),
            "template_labels": template_metadata.get("labels"),
            "serviceAccountName": template_spec.get("serviceAccountName"),
            "containers": self._compact_containers(template_spec.get("containers", []) or []),
            "initContainers": self._compact_containers(template_spec.get("initContainers", []) or []),
            "volumes": self._compact_volumes(template_spec.get("volumes", []) or []),
            "hostNetwork": template_spec.get("hostNetwork"),
            "hostPID": template_spec.get("hostPID"),
            "hostIPC": template_spec.get("hostIPC"),
        }

    def _compact_pod_spec(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "serviceAccountName": spec.get("serviceAccountName"),
            "containers": self._compact_containers(spec.get("containers", []) or []),
            "initContainers": self._compact_containers(spec.get("initContainers", []) or []),
            "volumes": self._compact_volumes(spec.get("volumes", []) or []),
            "hostNetwork": spec.get("hostNetwork"),
            "hostPID": spec.get("hostPID"),
            "hostIPC": spec.get("hostIPC"),
        }

    def _compact_pod_status(self, status: Dict[str, Any]) -> Dict[str, Any]:
        container_statuses = status.get("containerStatuses", []) or []

        compact_container_statuses = []

        for item in container_statuses[:5]:
            state = item.get("state", {}) or {}
            waiting = state.get("waiting", {}) or {}
            running = state.get("running", {}) or {}
            terminated = state.get("terminated", {}) or {}

            compact_container_statuses.append({
                "name": item.get("name"),
                "ready": item.get("ready"),
                "restartCount": item.get("restartCount"),
                "waiting_reason": waiting.get("reason"),
                "waiting_message": self._truncate(str(waiting.get("message", "")), 300),
                "running": bool(running),
                "terminated_reason": terminated.get("reason"),
                "exitCode": terminated.get("exitCode"),
            })

        return {
            "phase": status.get("phase"),
            "podIP": status.get("podIP"),
            "conditions": status.get("conditions"),
            "containerStatuses": compact_container_statuses,
        }

    def _compact_containers(self, containers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        compact = []

        for container in containers[:8]:
            env = container.get("env", []) or []
            env_from = container.get("envFrom", []) or []

            compact.append({
                "name": container.get("name"),
                "image": container.get("image"),
                "imagePullPolicy": container.get("imagePullPolicy"),
                "command": container.get("command"),
                "args": container.get("args"),
                "ports": container.get("ports"),
                "env_names": [
                    env_item.get("name")
                    for env_item in env
                    if isinstance(env_item, dict)
                ],
                "env_secret_refs": self._extract_secret_refs_from_env(env),
                "env_configmap_refs": self._extract_configmap_refs_from_env(env),
                "envFrom": env_from,
                "volumeMounts": container.get("volumeMounts"),
                "readinessProbe": self._compact_probe(container.get("readinessProbe")),
                "livenessProbe": self._compact_probe(container.get("livenessProbe")),
                "resources": container.get("resources"),
            })

        return compact

    def _compact_probe(self, probe: Any) -> Any:
        if not isinstance(probe, dict):
            return probe

        return {
            "httpGet": probe.get("httpGet"),
            "tcpSocket": probe.get("tcpSocket"),
            "exec": probe.get("exec"),
            "initialDelaySeconds": probe.get("initialDelaySeconds"),
            "periodSeconds": probe.get("periodSeconds"),
            "timeoutSeconds": probe.get("timeoutSeconds"),
            "failureThreshold": probe.get("failureThreshold"),
        }

    def _compact_volumes(self, volumes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        compact = []

        for volume in volumes[:10]:
            item = {"name": volume.get("name")}

            for key in [
                "secret",
                "configMap",
                "persistentVolumeClaim",
                "emptyDir",
                "hostPath",
                "projected",
                "cinder",
                "awsElasticBlockStore",
                "gcePersistentDisk",
                "azureDisk",
                "azureFile",
                "vsphereVolume",
                "rbd",
                "cephfs",
                "glusterfs",
                "iscsi",
                "nfs",
            ]:
                if key in volume:
                    item[key] = volume.get(key)

            compact.append(item)

        return compact

    def _extract_secret_refs_from_env(self, env: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        refs = []

        for env_item in env:
            if not isinstance(env_item, dict):
                continue

            value_from = env_item.get("valueFrom") or {}
            secret_ref = value_from.get("secretKeyRef")

            if secret_ref:
                refs.append({
                    "env": env_item.get("name"),
                    "name": secret_ref.get("name"),
                    "key": secret_ref.get("key"),
                })

        return refs

    def _extract_configmap_refs_from_env(self, env: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        refs = []

        for env_item in env:
            if not isinstance(env_item, dict):
                continue

            value_from = env_item.get("valueFrom") or {}
            config_ref = value_from.get("configMapKeyRef")

            if config_ref:
                refs.append({
                    "env": env_item.get("name"),
                    "name": config_ref.get("name"),
                    "key": config_ref.get("key"),
                })

        return refs

    def _run_early_healthcheck(self) -> str:
        if not self.health_checker or not self.target_namespace:
            return ""

        try:
            healthy, message = self.health_checker.check_health(
                self.target_namespace,
                timeout=self.early_healthcheck_timeout,
            )

            self._last_health_after_apply = {
                "healthy": healthy,
                "message": message,
            }

            if healthy:
                return (
                    "[SISTEMA]: HealthCheck pós-apply confirmou sucesso. "
                    f"{message}. Finalize a execução sem novas chamadas de ferramenta."
                )

            return (
                "[SISTEMA]: HealthCheck pós-apply ainda não confirmou estabilidade. "
                f"Mensagem: {message}. Use get_pod_diagnostics nos pods não prontos antes de reaplicar manifesto."
            )

        except Exception as exc:
            return (
                "[SISTEMA]: HealthCheck pós-apply não pôde ser executado. "
                f"Erro: {exc}. Continue com diagnóstico por ferramentas."
            )

    def _build_early_success_response(
        self,
        health_msg: str,
        tool_result: Any,
    ) -> str:
        result_message = ""

        if isinstance(tool_result, dict):
            result_message = str(tool_result.get("message", "") or "")

        return (
            "✅ Correção aplicada e validada com sucesso.\n\n"
            f"{health_msg.replace('[SISTEMA]: ', '')}\n\n"
            "O ambiente atingiu estado íntegro conforme HealthCheck. "
            "A execução foi encerrada antecipadamente para evitar iterações e consumo de tokens desnecessários.\n\n"
            f"Resultado do último apply_manifest: {self._truncate(result_message, 600)}"
        )

    def _safe_json_dumps(self, value: Any) -> str:
        try:
            return json.dumps(
                value,
                ensure_ascii=False,
                indent=2,
                default=str,
            )
        except Exception:
            return str(value)

    def _truncate(self, value: str, max_chars: int) -> str:
        if value is None:
            return ""

        text = str(value)

        if len(text) <= max_chars:
            return text

        return (
            text[:max_chars]
            + f"\n...[resultado truncado para {max_chars} caracteres para reduzir contexto]..."
        )

    def _hash_payload(self, payload: Any) -> str:
        serialized = self._safe_json_dumps(payload)
        return hashlib.md5(serialized.encode("utf-8")).hexdigest()

    def _hash_manifest(self, manifest: Any) -> str:
        text = str(manifest or "")
        normalized_lines = []

        for line in text.splitlines():
            stripped = line.strip()

            if not stripped:
                continue

            if stripped.startswith("#"):
                continue

            if "#" in stripped:
                stripped = re.sub(r"\s+#.*$", "", stripped).rstrip()

            normalized_lines.append(stripped)

        normalized = "\n".join(normalized_lines)
        return hashlib.md5(normalized.encode("utf-8")).hexdigest()

    def _extract_detected_issue_types(self, result: Any) -> set[str]:
        if not isinstance(result, dict):
            return set()

        detected_issues = result.get("detected_issues", [])

        if not isinstance(detected_issues, list):
            return set()

        return {
            str(issue.get("type"))
            for issue in detected_issues
            if isinstance(issue, dict) and issue.get("type")
        }

    def _append_history(
        self,
        history: List[Dict[str, str]],
        role: str,
        content: str,
        prune: bool = True,
    ) -> None:
        history.append({
            "role": role,
            "content": content,
        })

        if prune:
            self._prune_history(history)

    def _prune_history(self, history: List[Dict[str, str]]) -> None:
        if len(history) <= self.MAX_HISTORY_MESSAGES:
            return

        first_message = history[0]
        recent_messages = history[-(self.MAX_HISTORY_MESSAGES - 1):]

        history[:] = [first_message] + recent_messages

    def _compact_args_for_log(self, args: Dict[str, Any]) -> Dict[str, Any]:
        compact = {}

        for key, value in args.items():
            if key == "manifest":
                compact[key] = f"<manifesto com {len(str(value))} caracteres>"
            else:
                compact[key] = value

        return compact

    def _validate_reply_before_return(self, reply_content: str) -> str:
        """
        Impede que a LLM finalize dizendo que executou ferramenta ou aplicou
        manifesto sem que isso tenha ocorrido de fato no fluxo controlado.
        """
        content = (reply_content or "").lower()

        tool_names = [
            "list_resources",
            "get_resource_details",
            "get_pod_diagnostics",
            "get_pod_logs",
            "list_namespaces",
            "delete_resource",
            "scale_resource",
            "apply_manifest",
        ]

        claimed_tools = [
            tool_name
            for tool_name in tool_names
            if tool_name.lower() in content
        ]

        claims_tool_execution = any(
            marker in content
            for marker in [
                "executei:",
                "executei ",
                "apliquei",
                "aplicado com sucesso",
                "manifesto aplicado",
                "chamei a ferramenta",
                "usei a ferramenta",
            ]
        ) or bool(claimed_tools)

        claims_apply_success = any(
            marker in content
            for marker in [
                "manifesto aplicado",
                "aplicado com sucesso",
                "apliquei",
                "apply_manifest",
            ]
        )

        executed_tools = set(self._executed_tool_names)

        not_executed_claims = [
            tool_name
            for tool_name in claimed_tools
            if tool_name not in executed_tools
        ]

        if not_executed_claims:
            return (
                "[SISTEMA]: A resposta final foi bloqueada porque afirma execução de ferramenta "
                "sem chamada real correspondente. "
                f"Ferramentas alegadas e não executadas: {not_executed_claims}. "
                f"Ferramentas realmente executadas nesta rodada: {sorted(executed_tools)}. "
                "Use a ferramenta correta no formato de tool call ou responda sem declarar ações que não ocorreram."
            )

        if self._last_tool_error:
            return (
                "[SISTEMA]: A resposta final foi bloqueada porque a última chamada de ferramenta "
                f"falhou ou foi inválida. Ferramenta: {self._last_tool_error.get('tool_name')}. "
                f"Argumentos recebidos: {self._last_tool_error.get('args')}. "
                f"Erro: {self._last_tool_error.get('error')}. "
                "Corrija a chamada da ferramenta com todos os argumentos obrigatórios. "
                "Não afirme que executou uma ferramenta sem receber o resultado real dela."
            )

        if claims_apply_success and not self._last_apply_success:
            return (
                "[SISTEMA]: A resposta final foi bloqueada porque ela afirma que um manifesto foi aplicado, "
                "mas não houve chamada real bem-sucedida de apply_manifest na execução controlada. "
                "Chame apply_manifest com o YAML corrigido ou explique que ainda não aplicou nada. "
                "Não diga que aplicou o manifesto sem resultado real da ferramenta."
            )

        if claims_tool_execution and self._last_tool_name is None:
            return (
                "[SISTEMA]: A resposta final foi bloqueada porque afirma execução de ferramenta, "
                "mas nenhuma ferramenta foi executada nesta rodada. Use a ferramenta correta ou responda "
                "sem declarar ações que não ocorreram."
            )

        return ""

    def _execute_tool(self, tool_name: str, args: Dict[str, Any]):
        """
        Mapeamento entre a decisão da IA e a execução no adaptador K8s.
        """
        from src.application.use_cases.apply_manifest_command import ApplyManifestCommand
        from src.application.use_cases.delete_resource_command import DeleteResourceCommand
        from src.application.use_cases.get_pod_diagnostics_command import GetPodDiagnosticsCommand
        from src.application.use_cases.get_pod_logs_command import GetPodLogsCommand
        from src.application.use_cases.get_resource_details_command import GetResourceDetailsCommand
        from src.application.use_cases.list_namespaces_command import ListNamespacesCommand
        from src.application.use_cases.list_resources_command import ListResourcesCommand
        from src.application.use_cases.scale_resource_command import ScaleResourceCommand

        if tool_name == "list_resources":
            resource_types = args.get("resource_types", ["pods"])

            return ListResourcesCommand(self.k8s_adapter).execute(
                resource_types=resource_types,
                namespace=args.get("namespace", "default"),
            )

        if tool_name == "get_resource_details":
            missing = [
                field
                for field in ["resource_type", "name"]
                if not args.get(field)
            ]

            if missing:
                return {
                    "status": "ERROR",
                    "message": (
                        "Chamada inválida de get_resource_details. "
                        f"Campos obrigatórios ausentes: {missing}. "
                        "Use primeiro list_resources para obter o nome exato do recurso "
                        "e depois chame get_resource_details com resource_type, name e namespace."
                    ),
                }

            return GetResourceDetailsCommand(self.k8s_adapter).execute(
                args["resource_type"],
                args["name"],
                args.get("namespace", "default"),
            )

        if tool_name == "list_namespaces":
            return ListNamespacesCommand(self.k8s_adapter).execute()

        if tool_name == "get_pod_diagnostics":
            missing = [
                field
                for field in ["pod_name"]
                if not args.get(field)
            ]

            if missing:
                return {
                    "status": "ERROR",
                    "message": (
                        "Chamada inválida de get_pod_diagnostics. "
                        f"Campos obrigatórios ausentes: {missing}."
                    ),
                }

            return GetPodDiagnosticsCommand(self.k8s_adapter).execute(
                pod_name=args["pod_name"],
                namespace=args.get("namespace", "default"),
                tail_lines=args.get("tail_lines", 80),
            )

        if tool_name == "get_pod_logs":
            missing = [
                field
                for field in ["pod_name"]
                if not args.get(field)
            ]

            if missing:
                return {
                    "status": "ERROR",
                    "message": (
                        "Chamada inválida de get_pod_logs. "
                        f"Campos obrigatórios ausentes: {missing}."
                    ),
                }

            return GetPodLogsCommand(self.k8s_adapter).execute(
                args["pod_name"],
                args.get("namespace", "default"),
                args.get("tail_lines", 80),
            )

        if tool_name == "apply_manifest":
            manifest = args.get("manifest")
            target_namespace = args.get("namespace") or "default"

            if not manifest:
                return {
                    "status": "ERROR",
                    "message": "Conteúdo do parâmetro 'manifest' é obrigatório para execução.",
                }

            incoming_hash = self._hash_manifest(manifest)

            if incoming_hash == self._last_manifest_hash:
                return {
                    "status": "ERROR",
                    "message": (
                        "Manifesto idêntico ou praticamente igual já foi aplicado nesta execução. "
                        "Não reaplique em loop. Use get_pod_diagnostics no pod não pronto ou corrija apenas o campo responsável pela falha."
                    ),
                }

            return ApplyManifestCommand(self.k8s_adapter).execute(
                manifest=manifest,
                namespace=target_namespace,
            )

        if tool_name == "delete_resource":
            missing = [
                field
                for field in ["resource_type", "name"]
                if not args.get(field)
            ]

            if missing:
                return {
                    "status": "ERROR",
                    "message": (
                        "Chamada inválida de delete_resource. "
                        f"Campos obrigatórios ausentes: {missing}."
                    ),
                }

            return DeleteResourceCommand(self.k8s_adapter).execute(
                args["resource_type"],
                args["name"],
                args.get("namespace", "default"),
            )

        if tool_name == "scale_resource":
            missing = [
                field
                for field in ["resource_type", "name", "replicas"]
                if args.get(field) is None
            ]

            if missing:
                return {
                    "status": "ERROR",
                    "message": (
                        "Chamada inválida de scale_resource. "
                        f"Campos obrigatórios ausentes: {missing}."
                    ),
                }

            return ScaleResourceCommand(self.k8s_adapter).execute(
                args["resource_type"],
                args["name"],
                int(args["replicas"]),
                args.get("namespace", "default"),
            )

        return {
            "status": "ERROR",
            "message": f"Ferramenta '{tool_name}' não mapeada no executor do AgentService.",
        }

    def get_run_stats(self) -> Dict[str, Any]:
        return {
            "iterations": self._executed_iterations,
            "executed_tool_names": list(self._executed_tool_names),
            "last_apply_success": self._last_apply_success,
            "last_health_after_apply": self._last_health_after_apply,
        }

    def _now(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")