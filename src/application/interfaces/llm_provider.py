from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class LLMProviderInterface(ABC):
    """
    Contrato que qualquer provedor de IA (OpenAI, Ollama, Anthropic) deve seguir.
    """

    @abstractmethod
    def generate_text(self, prompt: str, system_instruction: str = None) -> str:
        """
        Gera uma resposta de texto simples (Chat).
        """
        pass

    @abstractmethod
    def decide_tool(self, 
                   messages: List[Dict[str, str]], # Mudamos de 'prompt: str' para 'messages'
                   tools_schema: List[Dict[str, Any]], 
                   system_instruction: str = None) -> Dict[str, Any]:
        pass