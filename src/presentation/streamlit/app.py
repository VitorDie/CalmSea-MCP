import streamlit as st
import os
import sys

# Garante que o Python encontre os módulos da raiz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

# Imports do Backend (Clean Arch)
from src.infrastructure.llm.openai_adapter import OpenAIAdapter
from src.infrastructure.k8s_adapter.service import K8sServiceAdapter
from src.infrastructure.llm.ollama_adapter import OllamaAdapter
from src.application.services.agent_service import AgentService

# Imports do Frontend (Atomic Design)
from src.presentation.streamlit.components.atoms import atom_title
from src.presentation.streamlit.components.organisms import organism_chat_window, organism_sidebar_status

# --- Configuração da Página ---
st.set_page_config(page_title="AgentK", page_icon="☸️", layout="wide")

# # --- Inicialização do Core (Singleton via Cache) ---
# @st.cache_resource
# def get_agent_core():
#     """
#     Inicializa o AgentService apenas uma vez.
#     """
#     try:
#         # Pega a chave do ambiente (certifique-se de ter exportado ou usar .env)
#         api_key = os.getenv("OPENAI_API_KEY")
#         if not api_key:
#             return None, "Falta OPENAI_API_KEY"
# 
#         llm = OpenAIAdapter(api_key=api_key)
#         k8s = K8sServiceAdapter() # Vai tentar conectar no Minikube
#         
#         agent = AgentService(llm, k8s)
#         return agent, None
#     except Exception as e:
#         return None, str(e)

def get_agent_core(provider_type: str, model_name: str):
    """
    Fábrica que cria o Agente com o cérebro escolhido.
    """
    try:
        if provider_type == "OpenAI":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key: return None, "Falta OPENAI_API_KEY"
            llm = OpenAIAdapter(api_key=api_key, model=model_name)
        
        elif provider_type == "Ollama (Local)":
            # Certifique-se de ter rodado: ollama pull llama3.1
            llm = OllamaAdapter(model=model_name)
            
        k8s = K8sServiceAdapter()
        return AgentService(llm, k8s), None

    except Exception as e:
        return None, str(e)

# --- SIDEBAR: Configuração ---
with st.sidebar:
    st.header("⚙️ Configuração IA")
    provider = st.selectbox("Provedor", ["OpenAI", "Ollama (Local)"])
    
    if provider == "OpenAI":
        model = st.text_input("Modelo", value="gpt-4o-mini")
    else:
        model = st.text_input("Modelo Local", value="llama3.1")
        st.caption("Certifique-se que o Ollama está rodando!")

# # Carrega o Agente
# agent, error = get_agent_core()

# Inicializa o agente com a escolha do usuário
agent, error = get_agent_core(provider, model)

# --- Renderização da Interface ---

# 1. Header
atom_title("AgentK Dashboard")

# 2. Sidebar (Status)
# organism_sidebar_status(is_connected=(agent is not None), model_name="GPT-4o-Mini")
organism_sidebar_status(is_connected=(agent is not None), model_name=f"{provider} / {model}")


# 3. Tratamento de Erro Inicial
if error:
    st.error(f"Falha na inicialização: {error}")
    st.stop()

# 4. Estado do Chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# 5. Renderiza Histórico (Organismo)
organism_chat_window(st.session_state.messages)

# 6. Input Loop (Interaction)
if prompt := st.chat_input("Ex: Liste os pods do namespace default..."):
    # A. Exibe mensagem do usuário
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # B. Processa resposta do Agente
    with st.chat_message("assistant"):
        with st.spinner("Consultando o Cluster..."):
            try:
                # CHAMA O SERVIÇO DE IA (O Cérebro)
                response = agent.run(prompt)
                
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"Erro ao processar: {e}")