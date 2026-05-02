# tests/unit/test_apply_manifest_command.py
import unittest
from unittest.mock import MagicMock
from src.application.use_cases.apply_manifest_command import ApplyManifestCommand

class TestApplyManifestCommand(unittest.TestCase):

    def test_execute_should_apply_manifest_successfully(self):
        # 1. ARRANGE
        mock_k8s_service = MagicMock()
        manifest = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {"name": "nginx"},
            "spec": {"containers": [{"name": "nginx", "image": "nginx"}]}
        }
        
        mock_return = {"metadata": {"name": "nginx"}, "status": "Created"}
        mock_k8s_service.apply_manifest.return_value = mock_return
        command = ApplyManifestCommand(mock_k8s_service)

        # 2. ACT
        result = command.execute(manifest=manifest, namespace="default")

        # 3. ASSERT - Ajustado para o novo wrapper de sucesso
        expected_result = {
            "status": "SUCCESS",
            "details": mock_return
        }
        self.assertEqual(result, expected_result)

if __name__ == "__main__":
    unittest.main()