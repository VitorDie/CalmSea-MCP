# tests/unit/test_delete_resource_command.py
import unittest
from unittest.mock import MagicMock
from src.application.use_cases.delete_resource_command import DeleteResourceCommand

class TestDeleteResourceCommand(unittest.TestCase):

    def test_execute_should_delete_resource(self):
        # 1. ARRANGE
        mock_k8s_service = MagicMock()
        
        # Simulamos que a deleção retornou sucesso (alguma mensagem ou objeto)
        mock_return = {"status": "Deleted", "details": "pod/nginx deleted"}
        mock_k8s_service.delete_resource.return_value = mock_return

        command = DeleteResourceCommand(mock_k8s_service)

        # 2. ACT
        result = command.execute(
            resource_type="pods",
            name="nginx-pod",
            namespace="default"
        )

        # 3. ASSERT
        self.assertEqual(result, mock_return)
        
        mock_k8s_service.delete_resource.assert_called_once_with(
            resource_type="pods",
            name="nginx-pod",
            namespace="default"
        )

if __name__ == "__main__":
    unittest.main()