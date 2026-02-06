# tests/unit/test_apply_manifest_command.py
import unittest
from unittest.mock import MagicMock
from src.application.use_cases.apply_manifest_command import ApplyManifestCommand

class TestApplyManifestCommand(unittest.TestCase):

    def test_execute_should_apply_manifest_successfully(self):
        # 1. ARRANGE
        mock_k8s_service = MagicMock()
        
        # Manifesto fake (ex: um Pod Nginx)
        manifest = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {"name": "nginx"},
            "spec": {"containers": [{"name": "nginx", "image": "nginx"}]}
        }
        
        # Simulamos que o K8s retorna o objeto criado
        mock_return = {"metadata": {"name": "nginx"}, "status": "Created"}
        mock_k8s_service.apply_manifest.return_value = mock_return

        command = ApplyManifestCommand(mock_k8s_service)

        # 2. ACT
        result = command.execute(manifest=manifest, namespace="default")

        # 3. ASSERT
        self.assertEqual(result, mock_return)
        
        # Verifica se o apply foi chamado corretamente
        mock_k8s_service.apply_manifest.assert_called_once_with(
            manifest=manifest,
            namespace="default"
        )

if __name__ == "__main__":
    unittest.main()