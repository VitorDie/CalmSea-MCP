import unittest
from unittest.mock import MagicMock, patch
from src.infrastructure.k8s_adapter.service import K8sServiceAdapter

class TestK8sServiceAdapter(unittest.TestCase):

    @patch('src.infrastructure.k8s_adapter.service.config')
    @patch('src.infrastructure.k8s_adapter.service.client')
    def test_list_pods_should_call_core_v1_api(self, mock_client, mock_config):
        """
        Testa se o método list_resources('pods') chama a API correta do Kubernetes.
        """
        # 1. ARRANGE
        # Configura o mock da API do Kubernetes
        mock_core_v1 = MagicMock()
        mock_client.CoreV1Api.return_value = mock_core_v1
        
        # Simula a resposta da API (uma lista de objetos com metadata.name)
        pod_1 = MagicMock()
        pod_1.metadata.name = "nginx-pod"
        mock_result = MagicMock()
        mock_result.items = [pod_1]
        
        mock_core_v1.list_namespaced_pod.return_value = mock_result

        # Inicializa o Adapter (o mock_config impede que ele tente ler ~/.kube/config real)
        adapter = K8sServiceAdapter()

        # 2. ACT
        result = adapter.list_resources('pods', 'default')

        # 3. ASSERT
        self.assertEqual(result, ["nginx-pod"])
        
        # Verifica se chamou a função exata da lib oficial
        mock_core_v1.list_namespaced_pod.assert_called_once_with('default')

    @patch('src.infrastructure.k8s_adapter.service.config')
    @patch('src.infrastructure.k8s_adapter.service.client')
    def test_should_handle_api_exception(self, mock_client, mock_config):
        # 1. ARRANGE
        mock_core_v1 = MagicMock()
        mock_client.CoreV1Api.return_value = mock_core_v1
        from kubernetes.client.rest import ApiException
        mock_core_v1.list_namespaced_pod.side_effect = ApiException(status=403, reason="Forbidden")

        adapter = K8sServiceAdapter()

        # 2. ACT
        result = adapter.list_resources('pods', 'default')

        # 3. ASSERT - Agora esperamos a mensagem de erro formatada
        self.assertEqual(result, ['Erro na API K8s: Forbidden (Status: 403)'])

if __name__ == "__main__":
    unittest.main()