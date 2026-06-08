import streamlit as st
import os
import sys
import time
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

# 2. Inicialização do Estado da Sessão (Controle de Batimento Cíclico)
if "calmsea_collector" not in st.session_state:
    st.session_state.calmsea_collector = TCCMetricsCollector(filename="results/calmsea_benchmark.csv")

if "loop_active" not in st.session_state:
    st.session_state.loop_active = False

if "last_scan" not in st.session_state:
    st.session_state.last_scan = "Nunca"

if "next_scan_timestamp" not in st.session_state:
    st.session_state.next_scan_timestamp = 0.0

# --- ORGANISMO: FÁBRICA DE GAUGE PLOTLY ---
def create_phantom_gauge(title, score):
    """Gera o velocímetro de integridade baseado no score calculado."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={'text': title, 'font': {'size': 18}},
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
    fig.update_layout(height=220, margin=dict(l=20, r=20, t=40, b=20))
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

# --- MOLÉCULA: SIDEBAR ---
with st.sidebar:
    st.title("🌊 CalmSea Config")
    provider_choice = st.selectbox("Provedor", ["OpenAI", "Ollama (Local)"])
    
    if provider_choice == "OpenAI":
        key = st.text_input("API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
        model_name = st.selectbox("Modelo", ["gpt-4o-mini", "o4-mini", "o1-mini"])
        base_adapter = OpenAIAdapter(api_key=key, model=model_name)
    else:
        model_name = st.selectbox("Modelo Local", ["qwen2.5-coder:7b", "llama3.1"])
        base_adapter = OllamaAdapter(model=model_name)

    intervalo = st.number_input("Intervalo entre análises (minutos)", min_value=1, max_value=60, value=2)
    
    # Botões de Controle do Estado do Loop (Corrigidos)
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("▶️ Iniciar", use_container_width=True):
            st.session_state.loop_active = True
            # Força a execução imediata na primeira iteração ao zerar o timestamp alvo
            st.session_state.next_scan_timestamp = 0.0
    with col_btn2:
        if st.button("⏹️ Parar", use_container_width=True):
            st.session_state.loop_active = False

    status_cor = "green" if st.session_state.loop_active else "red"
    st.markdown(f"Status: <span style='color:{status_cor}; font-weight:bold;'>{'EXECUTANDO' if st.session_state.loop_active else 'PARADO'}</span>", unsafe_allow_html=True)
    st.caption(f"Última Varredura: {st.session_state.last_scan}")

# 3. Preparação das ferramentas do Domínio
k8s = K8sServiceAdapter()
checker = K8sHealthChecker()
adapter = LLMMonitorDecorator(base_adapter, provider_choice, st.session_state.calmsea_collector)
agent = AgentService(adapter, k8s, health_checker=checker)

# --- TEMPLATE PRINCIPAL / DASHBOARD ---
st.title("CalmSea++ Autonomous SRE Engine")
st.markdown("---")

@st.fragment
def render_monitoring_panel():
    st.write(f"⏱️ *Última renderização do painel às: {datetime.now().strftime('%H:%M:%S')}*")
    
    # Executa a varredura real nos adaptadores de infraestrutura
    score_default, pods_default, trigger_def, msg_def = scan_namespace_health(k8s, "default")
    score_orion, pods_orion, trigger_orion, msg_orion = scan_namespace_health(k8s, "orion")
    
    score_cluster = int((score_default + score_orion) / 2)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.plotly_chart(create_phantom_gauge("Cluster Global Status", score_cluster), selection_mode="none")
    with col2:
        st.plotly_chart(create_phantom_gauge("Namespace: default", score_default), selection_mode="none")
    with col3:
        st.plotly_chart(create_phantom_gauge("Namespace: orion", score_orion), selection_mode="none")

    all_pods = pods_default + pods_orion
    st.markdown("### 📋 Mapeamento de Workloads Ativos")
    
    if all_pods:
        df_pods = pd.DataFrame(all_pods)
        st.dataframe(df_pods, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum workload ativo mapeado nos namespaces monitorados.")

    # --- CIRCUITO AUTÔNOMO DE INTERVENÇÃO (SRE AUTO-REMEDIAÇÃO CORRIGIDO) ---
    if st.session_state.loop_active:
        # Verifica se o timestamp atual ultrapassou o alvo configurado para disparar o agente
        if time.time() >= st.session_state.next_scan_timestamp:
            if trigger_def:
                st.toast(f"🚨 Anomalia em 'default'! Despertando AgentK...", icon="⚠️")
                with st.spinner("AgentK aplicando engenharia de correção em 'default'..."):
                    agent.run(user_prompt=(
                        f"O monitor passivo CalmSea detectou falhas no namespace 'default'. Causa: {msg_def}. "
                        "INSTRUÇÃO OBRIGATÓRIA: Remova o pod standalone problemático usando delete_resource. "
                        "Na sequência, use OBLIGATORIAMENTE a ferramenta apply_manifest para recriar o pod "
                        "com uma imagem válida (ex: nginx:latest). Não encerre a execução com um reply em texto "
                        "antes de efetivamente aplicar o novo manifesto via tool call."
                    ))
                st.toast("✅ Processo de remediação finalizado em 'default'!", icon="⚓")
                st.session_state.next_scan_timestamp = time.time() + (intervalo * 60)
                st.rerun()

            if trigger_orion:
                st.toast(f"🚨 Anomalia em 'orion'! Despertando AgentK...", icon="⚠️")
                with st.spinner("AgentK aplicando engenharia de correção em 'orion'..."):
                    agent.run(user_prompt=(
                        f"O monitor passivo CalmSea detectou falhas no namespace 'orion'. Causa: {msg_orion}. "
                        "INSTRUÇÃO OBRIGATÓRIA: Remova o pod standalone problemático usando delete_resource. "
                        "Na sequência, use OBLIGATORIAMENTE a ferramenta apply_manifest para recriar o pod "
                        "com uma imagem válida (ex: nginx:latest). Não encerre a execução com um reply em texto "
                        "antes de efetivamente aplicar o novo manifesto via tool call."
                    ))
                st.toast("✅ Processo de remediação finalizado em 'orion'!", icon="⚓")
                st.session_state.next_scan_timestamp = time.time() + (intervalo * 60)
                st.rerun()

            # Se rodou a checagem e estava tudo limpo (100% saudável)
            st.session_state.next_scan_timestamp = time.time() + (intervalo * 60)

render_monitoring_panel()

# --- 4. ORQUESTRADOR DE ALTA FREQUÊNCIA (HEARTBEAT LOOP) ---
if st.session_state.loop_active:
    # Em vez de travar por minutos, dorme apenas 1 segundo mantendo a UI responsiva
    time.sleep(1)
    st.session_state.last_scan = datetime.now().strftime("%H:%M:%S")
    st.rerun()