from typing import List, Dict, Any
from src.application.shared.command import Command
from src.application.interfaces.k8s_service_interface import K8sServiceInterface

class ListResourcesCommand(Command):
    def __init__(self, k8s_service: K8sServiceInterface):
        self.k8s_service = k8s_service

    def execute(self, resource_types: List[str], namespace: str = "default") -> Any:
        """
        Executa a listagem delegando para o adaptador polimórfico.
        """
        # Removemos o loop 'for' daqui, pois o K8sServiceAdapter 
        # agora já sabe iterar sobre a lista 'resource_types'.
        return self.k8s_service.list_resources(
            resource_types=resource_types, 
            namespace=namespace
        )