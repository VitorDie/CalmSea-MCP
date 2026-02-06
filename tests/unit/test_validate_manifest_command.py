# tests/unit/test_validate_manifest_command.py
import unittest
from unittest.mock import MagicMock
from src.application.use_cases.validate_manifest_command import ValidateManifestCommand

class TestValidateManifestCommand(unittest.TestCase):

    def test_execute_should_return_validation_result(self):
        # 1. ARRANGE
        mock_k8s_service = MagicMock()
        
        manifest = {
            "kind": "Pod",
            "metadata": {"name": "test-pod"}
        }
        
        # Simulamos que o K8s diz "Sim, é válido" (retorna o objeto que seria criado)
        mock_return = {"valid": True, "message": "Manifest is valid"}
        mock_k8s_service.validate_manifest.return_value = mock_return

        command = ValidateManifestCommand(mock_k8s_service)

        # 2. ACT
        result = command.execute(manifest=manifest, namespace="default")

        # 3. ASSERT
        self.assertEqual(result, mock_return)
        
        mock_k8s_service.validate_manifest.assert_called_once_with(
            manifest=manifest,
            namespace="default"
        )

if __name__ == "__main__":
    unittest.main()