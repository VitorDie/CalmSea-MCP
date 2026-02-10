# src/application/interfaces/llm_provider.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class LLMProviderInterface(ABC):
    @abstractmethod
    def generate_response(self, prompt: str, system_instruction: str = None) -> str:
        """Gera uma resposta simples de texto."""
        pass

    @abstractmethod
    def decide_tool(self, prompt: str, available_tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analisa o prompt e decide qual ferramenta chamar.
        Retorna: {'tool_name': 'list_pods', 'args': {'namespace': 'default'}}
        """
        pass