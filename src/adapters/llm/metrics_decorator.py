import time
import functools
from typing import Any, Dict

def monitor_performance(func):
    """
    Decorator para medir tempo de resposta e consumo de tokens.
    Respeita a Clean Architecture ao atuar como um Wrapper na camada de Adapters.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Dict[str, Any]:
        start_time = time.time()
        
        # Executa a chamada real ao modelo
        response = func(*args, **kwargs)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Extração de tokens baseada no formato comum de retorno (Ollama/OpenAI)
        # Se for uma string pura, inicializa tokens como 0 ou usa um contador simples
        tokens = 0
        if isinstance(response, dict):
            usage = response.get("usage", {})
            tokens = usage.get("total_tokens", usage.get("eval_count", 0))
        
        # Injeta as métricas no dicionário de resposta
        metrics = {
            "duration_seconds": round(duration, 4),
            "tokens": tokens,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        if isinstance(response, dict):
            response["performance_metrics"] = metrics
        
        return response

    return wrapper