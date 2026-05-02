from typing import List, Dict, Any

# Interfaces
from src.application.interfaces.llm_provider import LLMProviderInterface
from src.application.interfaces.k8s_service_interface import K8sServiceInterface

# Definições (O Menu de Ferramentas)
from src.application.tools_definitions import TOOLS_SCHEMA

# Commands (Ações de Infraestrutura)
from src.application.use_cases.list_resources_command import ListResourcesCommand
from src.application.use_cases.get_pod_logs_command import GetPodLogsCommand
from src.application.use_cases.list_namespaces_command import ListNamespacesCommand
from src.application.use_cases.get_resource_details_command import GetResourceDetailsCommand
from src.application.use_cases.delete_resource_command import DeleteResourceCommand
from src.application.use_cases.scale_resource_command import ScaleResourceCommand
from src.application.use_cases.apply_manifest_command import ApplyManifestCommand

class AgentService:
    def __init__(self, llm_provider: LLMProviderInterface, k8s_adapter: K8sServiceInterface):
        self.llm = llm_provider
        self.k8s_adapter = k8s_adapter
        
        # Personalidade focada em Realismo Radical e Engenharia de Operações Sênior
        self.system_instruction = (
            "Você é o AgentK, um Auditor de Segurança K8s e Engenheiro de Operações Sênior. "
            "Sua missão é a SÍNTESE DIALÉTICA: observar o erro (antítese) e executar a correção (síntese) sem hesitação. "
            "REGRAS DE SOBERANIA: "
            "1. AUTONOMIA DE MANIFESTO: Se você identificou um erro (como seletores desalinhados ou segredos expostos), é seu dever GERAR o YAML corrigido. Nunca chame 'apply_manifest' sem o argumento 'manifest' preenchido com o código YAML completo. "
            "2. MANIPULAÇÃO DE ESTADO: Ao corrigir recursos, remova metadados de runtime (uid, resourceVersion, creationTimestamp) para garantir uma aplicação limpa. "
            "3. AGNOSTICISMO DE NAMESPACE: Sempre extraia o namespace do recurso que você está auditando. Utilize esse mesmo namespace em todas as operações subsequentes (delete/apply). "
            "4. FLUXO DE RECON: Se um recurso não for encontrado (404) após uma deleção, considere isso um sinal verde para a RECONSTRUÇÃO imediata via 'apply_manifest'. "
            "Sua linguagem é técnica, precisa e voltada para a resiliência de produção. Zazen e faxina: limpe o cluster com a precisão de um sênior."
       )

    def run(self, user_prompt: str, system_instruction: str = None) -> str:
        history = [{"role": "user", "content": user_prompt}]
        max_iterations = 6 
        current_sys_instruction = system_instruction or self.system_instruction

        for i in range(max_iterations):
            # IMPORTANTE: Verifique se o seu Adapter realmente aceita 'messages'
            decision = self.llm.decide_tool(
                messages=history,
                tools_schema=TOOLS_SCHEMA,
                system_instruction=current_sys_instruction
            )

            print(f"\n--- ITERAÇÃO {i} ---")
            print(f"Decisão da IA: {decision}")

            action = decision.get("action")

            if action == "reply":
                return decision.get("content")

            elif action == "tool_use":
                tool_name = decision.get("tool_name")
                args = decision.get("tool_args", {})

                try:
                    # AGIR
                    result = self._execute_tool(tool_name, args)
                    
                    # A LINHA DA VERDADE
                    print(f"[DEBUG SOBERANIA] Resultado da {tool_name}: {result}")

                    # OBSERVAR: Injetamos a resposta para que a IA saiba que já agiu
                    # Adicionamos a fala do assistente (intenção) e o resultado (fato)
                    history.append({"role": "assistant", "content": f"Vou listar os recursos: {tool_name}"})
                    history.append({
                        "role": "user", 
                        "content": f"[SISTEMA]: Resultado de {tool_name}: {result}. Agora, responda ao usuário com base nisso."
                    })
                    
                except Exception as e:
                    print(f"❌ Erro na execução da tool: {e}")
                    history.append({"role": "user", "content": f"[ERRO]: {str(e)}"})
            
            else:
                return f"⚠️ Falha de Contexto: {decision.get('content')}"

        return "⚠️ Limite de soberania atingido: O Agente entrou em loop infinito."

    def _flatten_history(self, history: List[Dict[str, str]]) -> str:
        """
        Achata o histórico em uma string estruturada para respeitar a assinatura da interface.
        """
        return "\n".join([f"[{msg['role'].upper()}]: {msg['content']}" for msg in history])

    def _execute_tool(self, tool_name: str, args: Dict[str, Any]):
        """
        Mapeamento mecânico entre a decisão da IA e a execução no adaptador K8s.
        """

        # --- ETAPA DE RECON (LEITURA) ---
        if tool_name == "list_resources":
            r_types = args.get("resource_types", ["pods"])
            
            # Garante que r_types seja sempre uma lista para o Command
            if isinstance(r_types, str): 
                r_types = [r_types]
                
            # Chama o comando passando a lista estruturada
            return ListResourcesCommand(self.k8s_adapter).execute(
                resource_types=r_types, 
                namespace=args.get("namespace", "default")
            ) 

        elif tool_name == "get_resource_details":
            return GetResourceDetailsCommand(self.k8s_adapter).execute(
                args["resource_type"], args["name"], args["namespace"]
            )

        elif tool_name == "list_namespaces":
            return ListNamespacesCommand(self.k8s_adapter).execute()

        # --- ETAPA DE COMMIT/FIX (AÇÃO) ---
        elif tool_name == "apply_manifest":
            manifest = args.get("manifest")
            # Extraímos o namespace sem um default 'hardcoded' do projeto
            # Se a IA não passar, o comando falha e ela aprende que precisa passar
            target_namespace = args.get("namespace") or "default"
            
            if not manifest:
                return "Erro: Conteúdo do 'manifest' é obrigatório para execução."
            
            return ApplyManifestCommand(self.k8s_adapter).execute(
                manifest, target_namespace
            ) 

        elif tool_name == "delete_resource":
            return DeleteResourceCommand(self.k8s_adapter).execute(
                args["resource_type"], args["name"], args["namespace"]
            )

        elif tool_name == "scale_resource":
            return ScaleResourceCommand(self.k8s_adapter).execute(
                args["resource_type"], args["name"], int(args["replicas"]), args["namespace"]
            )

        elif tool_name == "get_pod_logs":
            return GetPodLogsCommand(self.k8s_adapter).execute(
                args["pod_name"], args["namespace"], args.get("tail_lines", 50)
            )

        return f"Erro: Ferramenta '{tool_name}' não mapeada no executor do AgentService."