# tests/unit/test_list_resources_command.py
import unittest
from unittest.mock import MagicMock

# Importação da classe que ainda vamos criar (vai dar erro na IDE, normal!)
from src.application.use_cases.list_resources_command import ListResourcesCommand

class TestListResourcesCommand(unittest.TestCase):

    def test_execute_should_return_grouped_resources(self):
        # 1. ARRANGE
        mock_k8s_service = MagicMock()
        
        # Ajustamos a lambda para ser genérica e aceitar os argumentos do comando
        mock_k8s_service.list_resources.side_effect = lambda resource_types, namespace: {
            t: [f"{t}-1"] for t in resource_types
        }

        command = ListResourcesCommand(k8s_service=mock_k8s_service)

        # 2. ACT
        result = command.execute(
            resource_types=["pods", "services"], 
            namespace="default"
        )

        # 3. ASSERT
        expected_result = {
            "pods": ["pods-1"],
            "services": ["services-1"]
        }
        self.assertEqual(result, expected_result)

if __name__ == "__main__":
    unittest.main()