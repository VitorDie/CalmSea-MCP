import streamlit as st
import os
import sys
import ollama
from openai import OpenAI
from datetime import datetime
from src.application.services.report_exporter import ReportExporter

# Caminhos do projeto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from src.infrastructure.llm.openai_adapter import OpenAIAdapter
from src.infrastructure.llm.ollama_adapter import OllamaAdapter
from src.infrastructure.k8s_adapter.service import K8sServiceAdapter
from src.application.services.agent_service import AgentService

st.set_page_config(page_title="AgentK Dashboard", page_icon="☸️", layout="wide")

def get_openai_models(api_key):
    try:
        client = OpenAI(api_key=api_key)
        models = client.models.list()
        # Filtra por gpt, o1 e a nova série o4 para o benchmark
        return sorted([m.id for m in models.data if any(x in m.id for x in ["gpt", "o1", "o4"])], reverse=True)
    except:
        return ["o4-mini", "o1-mini", "gpt-4o-mini"]

def get_ollama_models():
    try:
        response = ollama.list()
        # Na v0.1.0+, response é um objeto ListResponse com atributo 'models'
        if hasattr(response, 'models'):
            return [m.model for m in response.models]
        # Fallback para versões legadas/dicionário
        return [m['name'] for m in response.get('models', [])]
    except Exception as e:
        # Debug útil para o console do Streamlit
        print(f"[DEBUG] Erro ao listar Ollama: {e}")
        return [""]

with st.sidebar:
    st.title("⚙️ Configuração")
    provider = st.selectbox("Provedor", ["OpenAI", "Ollama (Local)"])
    
    if provider == "OpenAI":
        key = st.text_input("API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
        model = st.selectbox("Modelo", get_openai_models(key))
        adapter = OpenAIAdapter(api_key=key, model=model)
    else:
        model = st.selectbox("Modelo Local", get_ollama_models())
        adapter = OllamaAdapter(model=model)

# Fábrica do Agente
k8s = K8sServiceAdapter()
agent = AgentService(adapter, k8s)

st.title("AgentK++")
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Comando de SRE..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Processando..."):
            # 1. O Agente executa a ação
            response = agent.run(prompt)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

            # 2. "Faxina" Pós-Resposta: Captura o estado real do cluster para o relatório
            # Usamos o seu k8s adapter para pegar o snapshot (get all)
            # Dica: você pode tentar extrair o namespace do prompt ou usar um padrão
            target_ns = "default" 
            try:
                # Aqui usamos o comando que você já usa no persist_results
                verify_output = os.popen(f"kubectl get all -n {target_ns}").read()
            except:
                verify_output = "Não foi possível capturar o estado do cluster."

            # 3. Gera o Markdown usando a Classe Unificada
            md_report = ReportExporter.generate_markdown(
                model=model,
                res=response,
                is_ok=True, # No manual, o usuário decide, mas marcamos como True para o template
                health_msg="Interação via Dashboard (Manual)",
                ns=target_ns,
                verify_output=verify_output,
                yaml_name="Chat_Interativo"
            )

            # 4. O Botão de Exportação
            st.download_button(
                label="📥 Baixar Relatório de SRE (.md)",
                data=md_report,
                file_name=f"Relatorio_AgentK_{datetime.now().strftime('%H%M%S')}.md",
                mime="text/markdown",
                help="Clique para baixar o diagnóstico formatado para o TCC."
            )