import os
import json
from typing import List, Dict, Any
from openai import OpenAI, OpenAIError
from src.application.interfaces.llm_provider import LLMProviderInterface

class OpenAIAdapter(LLMProviderInterface):
    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("API Key da OpenAI não encontrada!")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        self.last_full_response = {} 

    def generate_text(self, prompt: str, system_instruction: str = None) -> str:
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        kwargs = {"model": self.model, "messages": messages}
        if not self.model.startswith("o"):
            kwargs["temperature"] = 0.7

        try:
            response = self.client.chat.completions.create(**kwargs)
            self.last_full_response = response 
            return response.choices[0].message.content
        except OpenAIError as e:
            return f"Erro OpenAI: {str(e)}"

    def decide_tool(self, messages: List[Dict[str, str]], tools_schema: List[Dict[str, Any]], system_instruction: str = None) -> Dict[str, Any]:
        # Constrói o payload de mensagens corretamente
        api_messages = []
        if system_instruction:
            api_messages.append({"role": "system", "content": system_instruction})
        
        # Adiciona o histórico que já vem formatado
        api_messages.extend(messages)

        kwargs = {
            "model": self.model,
            "messages": api_messages,
            "tools": tools_schema,
            "tool_choice": "auto",
            "temperature": 0.0 # Determinismo total
        }

        try:
            response = self.client.chat.completions.create(**kwargs)
            self.last_full_response = response 
            message = response.choices[0].message
            
            if message.tool_calls:
                selected_tool = message.tool_calls[0]
                return {
                    "action": "tool_use",
                    "tool_name": selected_tool.function.name,
                    "tool_args": json.loads(selected_tool.function.arguments)
                }
            return {"action": "reply", "content": message.content}
        except Exception as e:
            return {"action": "error", "content": str(e)}