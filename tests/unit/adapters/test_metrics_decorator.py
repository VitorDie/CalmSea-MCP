import unittest
from unittest.mock import MagicMock, patch
import time
from src.adapters.llm.metrics_decorator import monitor_performance

class TestMetricsDecorator(unittest.TestCase):
    def test_should_measure_execution_time_and_token_count(self):
        # Arrange
        # Simulamos uma função que seria a chamada real ao LLM (Ollama/OpenAI)
        mock_response = {
            "text": "Resposta de teste",
            "usage": {"total_tokens": 50}
        }
        
        @monitor_performance
        def fake_llm_call(prompt):
            time.sleep(0.1)  # Simula um delay de processamento
            return mock_response

        # Act
        # Executamos a função decorada
        result = fake_llm_call("Olá, AgentK")

        # Assert
        # Verificamos se o resultado original foi mantido
        self.assertEqual(result["text"], "Resposta de teste")
        
        # Verificamos se o decorador injetou os metadados de performance no retorno
        self.assertIn("performance_metrics", result)
        self.assertGreaterEqual(result["performance_metrics"]["duration_seconds"], 0.1)
        self.assertEqual(result["performance_metrics"]["tokens"], 50)

if __name__ == '__main__':
    unittest.main()