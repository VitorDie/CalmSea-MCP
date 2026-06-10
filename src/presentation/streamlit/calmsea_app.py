import streamlit as st
import os
import sys
import time
import ollama
from openai import OpenAI
from datetime import datetime
import plotly.graph_objects as go
import pandas as pd

# 1. Ajuste de Caminhos do Projeto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from src.infrastructure.llm.openai_adapter import OpenAIAdapter
from src.infrastructure.llm.ollama_adapter import OllamaAdapter
from src.adapters.llm.metrics_decorator import LLMMonitorDecorator
from src.infrastructure.metrics.collector import TCCMetricsCollector
from src.infrastructure.k8s_adapter.service import K8sServiceAdapter
from src.infrastructure.k8s_adapter.health_checker import K8sHealthChecker
from src.application.services.agent_service import AgentService

st.set_page_config(page_title="CalmSea SRE Monitor", page_icon="🌊", layout="wide")

# 2. Inicialização do Estado da Sessão (Controle de Batimento Cíclico e Cache)
if "calmsea_collector" not in st.session_state:
    st.session_state.calmsea_collector = TCCMetricsCollector(filename="results/calmsea_benchmark.csv")

if "loop_active" not in st.session_state:
    st.session_state.loop_active = False

if "last_scan" not in st.session_state:
    st.session_state.last_scan = "Nunca"

if "next_scan_timestamp" not in st.session_state:
    st.session_state.next_scan_timestamp = 0.0

# CORREÇÃO VISUAL: Inicialização de chaves de cache para evitar "piscadas" na UI
if "cached_ollama_models" not in st.session_state:
    st.session_state.cached_ollama_models = []

if "cached_openai_models" not in st.session_state:
    st.session_state.cached_openai_models = []

# --- HELPER: DESCOBERTA DINÂMICA DE MODELOS ---
def get_openai_models(api_key):
    try:
        client = OpenAI(api_key=api_key)
        models = client.models.list()
        return sorted([m.id for m in models.data if any(x in m.id for x in ["gpt", "o1", "o4"])], reverse=True)
    except:
        return ["o4-mini", "o1-mini", "gpt-4o-mini"]

def get_ollama_models():
    try:
        response = ollama.list()
        if hasattr(response, 'models'):
            return [m.model for m in response.models]
        return [m['name'] for m in response.get('models', [])]
    except Exception:
        return ["qwen2.5:3b"]

# --- ORGANISMO: FÁBRICA DE GAUGE PLOTLY ---
def create_phantom_gauge(title, score):
    """Gera o velocímetro de integridade baseado no score calculado."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={'text': title, 'font': {'size': 16}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "#1f77b4"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 40], 'color': '#ff4d4d'},
                {'range': [40, 80], 'color': '#ffa64d'},
                {'range': [80, 100], 'color': '#2db300'}
            ],
        }
    ))
    fig.update_layout(height=200, margin=dict(l=10, r=10, t=35, b=10))
    return fig

# --- ENGINE: CÁLCULO DE SCORE E DIAGNÓSTICO REAL ---
def scan_namespace_health(k8s_adapter, ns):
    """Varre o namespace coletando diagnósticos reais do cluster."""
    pod_names = k8s_adapter.list_resources(resource_types="pods", namespace=ns)
    
    if not pod_names or (isinstance(pod_names, list) and len(pod_names) == 0):
        return 100, [], False, ""
        
    if isinstance(pod_names, dict) and "error" in pod_names:
        return 0, [], False, f"Erro na API: {pod_names['error']}"

    pods_table_rows = []
    total_pods = len(pod_names)
    unhealthy_pods = 0
    remediation_trigger = False
    critical_msg = ""

    for name in pod_names:
        diag = k8s_adapter.get_pod_diagnostics(pod_name=name, namespace=ns)
        
        if diag.get("status") == "SUCCESS":
            phase = diag.get("phase")
            issues = diag.get("detected_issues", [])
            
            has_issues = len(issues) > 0 or phase in ["Failed", "Unknown"]
            
            if has_issues:
                unhealthy_pods += 1
                status_text = f"❌ Unhealthy ({phase})"
                remediation_trigger = True
                if issues:
                    critical_msg = issues[0].get("message", "Falha estrutural ativa.")
                else:
                    critical_msg = diag.get("probable_root_cause", f"Pod {name} instável.")
            else:
                status_text = "✅ Healthy"
                
            pods_table_rows.append({
                "Pod": name,
                "Namespace": ns,
                "Health": status_text
            })

    if total_pods > 0:
        score = int(((total_pods - unhealthy_pods) / total_pods) * 100)
    else:
        score = 100

    return score, pods_table_rows, remediation_trigger, critical_msg

# --- MOLÉCULA: SIDEBAR (CONFIGURAÇÕES DINÂMICAS E CACHEADAS) ---
with st.sidebar:
    logo_path = "docs/calmsea_logo.png"
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    else:
        st.info("🌊 CalmSea")
    
    st.title("⚙️ Configuração")
    provider_choice = st.selectbox("Provedor", ["OpenAI", "Ollama (Local)"])
    
    if provider_choice == "OpenAI":
        key = st.text_input("API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
        
        # CORREÇÃO VISUAL: Só busca da API se o estado de cache estiver em branco
        if not st.session_state.cached_openai_models and key:
            st.session_state.cached_openai_models = get_openai_models(key)
            
        model_options = st.session_state.cached_openai_models if st.session_state.cached_openai_models else ["gpt-4o-mini", "o4-mini"]
        model_name = st.selectbox("Modelo", model_options)
        base_adapter = OpenAIAdapter(api_key=key, model=model_name)
    else:
        # CORREÇÃO VISUAL: Cache da listagem do Ollama para travar o flicker da tela
        if not st.session_state.cached_ollama_models:
            st.session_state.cached_ollama_models = get_ollama_models()
            
        model_name = st.selectbox("Modelo Local", st.session_state.cached_ollama_models)
        base_adapter = OllamaAdapter(model=model_name)

    intervalo = st.number_input("Intervalo entre análises (minutos)", min_value=1, max_value=60, value=2)
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("▶️ Iniciar", use_container_width=True):
            st.session_state.loop_active = True
            st.session_state.next_scan_timestamp = 0.0
    with col_btn2:
        if st.button("⏹️ Parar", use_container_width=True):
            st.session_state.loop_active = False

    status_cor = "green" if st.session_state.loop_active else "red"
    st.markdown(f"Status: <span style='color:{status_cor}; font-weight:bold;'>{'EXECUTANDO' if st.session_state.loop_active else 'PARADO'}</span>", unsafe_allow_html=True)
    st.caption(f"Última Varredura: {st.session_state.last_scan}")

# 3. Preparação das ferramentas base da Infraestrutura
k8s = K8sServiceAdapter()
checker = K8sHealthChecker()
adapter = LLMMonitorDecorator(base_adapter, provider_choice, st.session_state.calmsea_collector)

# --- TEMPLATE PRINCIPAL / DASHBOARD ---
st.title("CalmSea Autonomous SRE Engine")
st.markdown("---")

@st.fragment
def render_monitoring_panel():
    st.write(f"⏱ *Última verificação interna às: {datetime.now().strftime('%H:%M:%S')}*")
    
    # CORREÇÃO DINÂMICA: Descoberta em tempo real de todos os namespaces ativos no Minikube
    namespaces_reais = k8s.list_namespaces()
    
    if not namespaces_reais:
        namespaces_reais = ["default"] # Fallback de segurança
        
    scores_dict = {}
    all_pods_accumulated = []
    
    # Varredura paralela/cíclica em lote coletando scores de saúde
    for ns in namespaces_reais:
        score_ns, pods_ns, trigger_ns, msg_ns = scan_namespace_health(k8s, ns)
        scores_dict[ns] = {
            "score": score_ns,
            "trigger": trigger_ns,
            "message": msg_ns
        }
        all_pods_accumulated.extend(pods_ns)
        
    # Média global ponderada pela quantidade de namespaces descobertos
    score_cluster = int(sum(item["score"] for item in scores_dict.values()) / len(scores_dict))

    # CORREÇÃO DINÂMICA: Montagem do Grid de Velocímetros (Gauge Central + N Colunas Dinâmicas)
# 2. Renderização do Gauge Principal
    st.plotly_chart(create_phantom_gauge("Cluster Global Status", score_cluster), selection_mode="none")
    
    st.markdown("#### ☸️ Distribuição por Namespaces Ativos")
    
    # CORREÇÃO VISUAL: Grid responsivo com quebra de linha (Máximo 3 colunas por linha)
    MAX_COLS = 3
    namespaces_lista = list(namespaces_reais)
    
    # Divide a lista de namespaces em grupos de no máximo MAX_COLS
    for i in range(0, len(namespaces_lista), MAX_COLS):
        grupo_ns = namespaces_lista[i:i + MAX_COLS]
        cols_namespaces = st.columns(len(grupo_ns)) # Cria colunas apenas para o grupo atual
        
        for idx, ns in enumerate(grupo_ns):
            with cols_namespaces[idx]:
                # Criamos um container visual estruturado para cada velocímetro
                with st.container(border=True):
                    st.plotly_chart(
                        create_phantom_gauge(f"NS: {ns}", scores_dict[ns]["score"]), 
                        selection_mode="none",
                        use_container_width=True # FORÇA o Plotly a respeitar a largura da coluna
                    )

    # 3. Tabela Consolidada Unificada de Pods
    st.markdown("### 📋 Mapeamento de Workloads Ativos")
    if all_pods_accumulated:
        df_pods = pd.DataFrame(all_pods_accumulated)
        st.dataframe(df_pods, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum workload ativo mapeado nos namespaces monitorados.")

    # --- SOBERANIA OPERACIONAL: CIRCUITO DE AUTO-REMEDIAÇÃO AMARRADO ---
    if st.session_state.loop_active:
        if time.time() >= st.session_state.next_scan_timestamp:
            
            # Varre os gatilhos dinamicamente. Se algum namespace cair, o AgentK acorda focado nele
            for ns in namespaces_reais:
                if scores_dict[ns]["trigger"]:
                    msg_erro = scores_dict[ns]["message"]
                    st.toast(f"🚨 Anomalia em '{ns}'! Despertando AgentK...", icon="⚠️")
                    
                    # Cria o serviço injetando o namespace dinâmico no construtor
                    agent_dinamico = AgentService(adapter, k8s, health_checker=checker, target_namespace=ns)
                    
                    with st.spinner(f"AgentK aplicando engenharia de correção em '{ns}'..."):
                        agent_dinamico.run(user_prompt=(
                            f"O monitor passivo CalmSea detectou falhas estruturais no namespace '{ns}'. Causa raiz provável: {msg_erro}. "
                            f"DIRETRIZ DE SEGURANÇA E POLÍTICA DE NOMENCLATURA INVIOLÁVEL:\n"
                            f"1. Você deve operar ESTREITAMENTE dentro do namespace '{ns}'.\n"
                            f"2. Execute delete_resource para remover o pod standalone problemático informando explicitamente namespace='{ns}'.\n"
                            f"3. Use a ferramenta apply_manifest para recriar o recurso mantendo EXATAMENTE o tipo 'kind: Pod' e o nome original 'name: pod-quebrado-tcc'.\n"
                            f"4. É PROIBIDO migrar para Deployment ou alterar o nome do recurso. Substitua apenas a imagem por uma versão válida e estável (ex: nginx:latest) dentro da especificação do Pod original. Não encerre sem a tool call."
                        ))
                    st.toast(f"✅ Ambiente estabilizado em '{ns}'!", icon="⚓")
                    st.session_state.next_scan_timestamp = time.time() + (intervalo * 60)
                    st.rerun()

            st.session_state.next_scan_timestamp = time.time() + (intervalo * 60)

render_monitoring_panel()

# --- 4. ORQUESTRADOR DE ALTA FREQUÊNCIA (HEARTBEAT LOOP) ---
if st.session_state.loop_active:
    time.sleep(1)
    st.session_state.last_scan = datetime.now().strftime("%H:%M:%S")
    st.rerun()