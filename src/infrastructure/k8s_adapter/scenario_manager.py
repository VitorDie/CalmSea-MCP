import os
import time
import json
import logging

logger = logging.getLogger("ScenarioManager")

class K8sScenarioManager:
    def __init__(self):
        self.ns_map = {
            "1-orion": "teste-orion", "2-frontend": "teste-frontend",
            "3-mysql": "teste-mysql", "4-vllm": "teste-vllm",
            "5-nginx": "teste-nginx", "6-selenium": "teste-selenium",
            "7-elasticsearch": "teste-elasticsearch", "8-newrelic": "teste-newrelic",
            "9-storm": "teste-storm", "10-mongodb": "teste-mongodb", 
            "fiware-minikube": "teste-fiware-minikube"
        }

    def prepare(self, yaml_file):
        base = yaml_file.replace(".yaml", "")
        ns = self.ns_map.get(base, "default")
        
        # 1. FAXINA RADICAL (Destruição com Verificação)
        self._ensure_absolute_cleanup(ns)
        
        # 2. COOLDOWN DE ESTABILIZAÇÃO (Física dos Sistemas)
        # Dá tempo para o API Server do Minikube consolidar a limpeza no etcd
        time.sleep(5)
        
        # 3. RECONSTRUÇÃO DO TERRITÓRIO
        print(f"[*] Criando namespace virgem: {ns}")
        os.system(f"kubectl create namespace {ns} > /dev/null 2>&1")
        
        # Espera curta para o K8s injetar o default service account
        time.sleep(2)
        
        # 4. APLICAÇÃO DO CENÁRIO
        print(f"[*] Aplicando cenário: {yaml_file}")
        path = f"docs/tests/scenarios/{yaml_file}"
        exit_code = os.system(f"kubectl apply -f {path} -n {ns} > /dev/null 2>&1")
        
        if exit_code != 0:
            print(f"[❌] Falha crítica ao aplicar {yaml_file} em {ns}.")
        else:
            # Tempo para o Scheduler do K8s criar as instâncias iniciais dos Pods
            time.sleep(5)
            print(f"[✅] Ambiente {ns} pronto para o AgentK.")
            
        return ns

    def _ensure_absolute_cleanup(self, ns):
        """Garante que o namespace e seus fantasmas foram expurgados."""
        print(f"[*] Purgando namespace {ns}...")
        
        # Tenta o delete normal primeiro
        os.system(f"kubectl delete namespace {ns} --ignore-not-found --grace-period=0 --force > /dev/null 2>&1")
        
        retries = 0
        max_retries = 30 # 60 segundos totais
        
        while True:
            # Verifica se o namespace ainda existe no domínio do real
            check = os.popen(f"kubectl get ns {ns} 2>&1").read()
            
            if "NotFound" in check:
                print(f"[+] Namespace {ns} purgado com sucesso.")
                break
                
            if retries >= max_retries:
                print(f"[!] Namespace {ns} travado em 'Terminating'. Forçando remoção de finalizers...")
                self._force_remove_finalizers(ns)
                break
            
            print(f"[⏳] Aguardando limpeza física de {ns} ({retries*2}s)...")
            time.sleep(2)
            retries += 1

    def _force_remove_finalizers(self, ns):
        """Técnica avançada: Remove finalizers que impedem a deleção do namespace."""
        cmd = (
            f"kubectl get namespace {ns} -o json | "
            "jq '.spec.finalizers = []' | "
            f"kubectl replace --raw /api/v1/namespaces/{ns}/finalize -f -"
        )
        os.system(cmd + " > /dev/null 2>&1")
        time.sleep(5)

    def get_live_yaml(self, ns, yaml_path):
        """Extrai o estado atual dos recursos para análise da LLM."""
        # Se o recurso foi deletado pelo AgentK, o comando pode falhar. Tratamos isso aqui.
        cmd = f"kubectl get -f {yaml_path} -n {ns} -o yaml 2>/dev/null"
        result = os.popen(cmd).read()
        return result if result else "# Recurso não encontrado no cluster."