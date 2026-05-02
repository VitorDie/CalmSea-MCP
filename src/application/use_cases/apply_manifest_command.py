import yaml
from typing import Dict, Any, Union
from src.application.shared.command import Command
from src.application.interfaces.k8s_service_interface import K8sServiceInterface

class ApplyManifestCommand(Command):
    def __init__(self, k8s_service: K8sServiceInterface):
        self.k8s_service = k8s_service

    def execute(self, manifest: Union[str, Dict[str, Any]], namespace: str = "default") -> Dict[str, Any]:
        """
        Executa a síntese de um ou mais manifestos no cluster.
        Suporta strings com múltiplos documentos (separados por ---).
        """
        try:
            # 1. Se for string, precisamos parsear. 
            # Usamos safe_load_all para suportar o stream (---) que causou o erro.
            if isinstance(manifest, str):
                manifests = list(yaml.safe_load_all(manifest))
            else:
                manifests = [manifest]

            results = []
            for m in manifests:
                if not m: continue # Pula documentos vazios
                
                # 2. Delegação Soberana para o serviço
                res = self.k8s_service.apply_manifest(
                    manifest=m,
                    namespace=namespace
                )
                results.append(res)

            return {
                "status": "SUCCESS",
                "details": results if len(results) > 1 else results[0]
            }

        except Exception as e:
            return {
                "status": "ERROR", 
                "message": f"Falha na síntese do manifesto: {str(e)}"
            }