import os

class K8sScenarioManager:
    def __init__(self):
        self.ns_map = {
            "1-orion": "teste-orion", "2-frontend": "teste-frontend",
            "3-mysql": "teste-mysql", "4-vllm": "teste-vllm",
            "5-nginx": "teste-nginx", "6-selenium": "teste-selenium",
            "7-elasticsearch": "teste-elasticsearch", "8-newrelic": "teste-newrelic",
            "9-storm": "teste-storm", "10-mongodb": "teste-mongodb", "fiware-minikube" : "teste-fiware-minikube"
        }

    def prepare(self, yaml_file):
        base = yaml_file.replace(".yaml", "")
        ns = self.ns_map.get(base, "default")
        
        # Correção 2.2: Limpeza isolada por Namespace
        os.system(f"kubectl delete namespace {ns} --ignore-not-found")
        os.system(f"kubectl create namespace {ns}")
        
        # Aplica o cenário vulnerável no namespace correto
        os.system(f"kubectl apply -f docs/tests/scenarios/{yaml_file} -n {ns}")
        return ns

    def get_live_yaml(self, ns, yaml_path):
        # Correção 1: Introspecção (Puxa o YAML real que está rodando)
        cmd = f"kubectl get -f {yaml_path} -n {ns} -o yaml"
        return os.popen(cmd).read()