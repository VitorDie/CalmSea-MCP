import ollama
import json
import re
from typing import List, Dict, Any
from src.application.interfaces.llm_provider import LLMProviderInterface

class OllamaAdapter(LLMProviderInterface):
    def __init__(self, model: str = "llama3.1"):
        self.model = model
        self.last_full_response = {}

    def generate_text(self, prompt: str, system_instruction: str = None) -> str:
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        try:
            response = ollama.chat(model=self.model, messages=messages)
            self.last_full_response = response 
            return response['message']['content']
        except Exception as e:
            return f"Erro Ollama: {str(e)}"

    def decide_tool(self, prompt: str, tools_schema: List[Dict[str, Any]], system_instruction: str = None) -> Dict[str, Any]:
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        try:
            # Importante: Ollama precisa de suporte a tools no binário (v0.3.0+)
            response = ollama.chat(
                model=self.model,
                messages=messages,
                tools=tools_schema
            )
            self.last_full_response = response 

            message = response['message']
            if 'tool_calls' in message and message['tool_calls']:
                tool_call = message['tool_calls'][0]
                args = tool_call['function']['arguments']
                
                # Se o Ollama devolver string em vez de dict, forçamos o parse
                if isinstance(args, str):
                    args = json.loads(args)

                return {
                    "action": "tool_use",
                    "tool_name": tool_call['function']['name'],
                    "tool_args": args
                }

            return {"action": "reply", "content": message['content']}
        except Exception as e:
            return {"action": "error", "content": str(e)}