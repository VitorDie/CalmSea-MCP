# src/application/tools_definitions.py

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "list_resources",
            "description": "Lista recursos do Kubernetes (pods, services, deployments) em um namespace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "resource_types": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["pods", "services", "deployments", "nodes"]},
                        "description": "Lista de tipos de recursos para buscar."
                    },
                    "namespace": {"type": "string", "description": "O namespace do Kubernetes."}
                },
                "required": ["resource_types", "namespace"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_resource_details",
            "description": "Obtém detalhes completos (YAML/JSON) de um recurso específico.",
            "parameters": {
                "type": "object",
                "properties": {
                    "resource_type": {"type": "string", "description": "Tipo do recurso (ex: pod, service)."},
                    "name": {"type": "string", "description": "Nome do recurso."},
                    "namespace": {"type": "string", "description": "Namespace do recurso."}
                },
                "required": ["resource_type", "name", "namespace"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_pod_logs",
            "description": "Retorna os logs de um pod específico.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pod_name": {"type": "string", "description": "Nome exato do pod."},
                    "namespace": {"type": "string", "description": "Namespace onde o pod está."},
                    "tail_lines": {"type": "integer", "description": "Linhas finais (padrão 50)."}
                },
                "required": ["pod_name", "namespace"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_namespaces",
            "description": "Lista todos os namespaces disponíveis no cluster.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_resource",
            "description": "Remove um recurso do cluster (CUIDADO: Ação destrutiva).",
            "parameters": {
                "type": "object",
                "properties": {
                    "resource_type": {"type": "string", "description": "Tipo do recurso (ex: pod)."},
                    "name": {"type": "string", "description": "Nome do recurso a deletar."},
                    "namespace": {"type": "string", "description": "Namespace do recurso."}
                },
                "required": ["resource_type", "name", "namespace"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scale_resource",
            "description": "Escala o número de réplicas de um Deployment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "resource_type": {"type": "string", "description": "Geralmente 'deployment'."},
                    "name": {"type": "string", "description": "Nome do deployment."},
                    "replicas": {"type": "integer", "description": "Novo número de réplicas desejado."},
                    "namespace": {"type": "string", "description": "Namespace do recurso."}
                },
                "required": ["resource_type", "name", "replicas", "namespace"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "apply_manifest",
            "description": "Aplica um manifesto Kubernetes (YAML/JSON) diretamente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "manifest": {"type": "object", "description": "O dicionário representando o manifesto YAML/JSON."},
                    "namespace": {"type": "string", "description": "Namespace alvo."}
                },
                "required": ["manifest", "namespace"]
            }
        }
    }
]