import streamlit as st
import os
import sys
import time
import ollama
import json
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
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "#1f77b4"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {"range": [0, 40], "color": "#ff4d4d"},
                {"range": [40, 80], "color": "#ffa64d"},
                {"range": [80, 100], "color": "#2db300"}
            ],
        }
    ))
    fig.update_layout(height=150, margin=dict(l=10, r=10, t=10, b=10))
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
    st.title("🌊 CalmSea Config")
    provider_choice = st.selectbox("Provedor", ["OpenAI", "Ollama (Local)"])
    
    if provider_choice == "OpenAI":
        key = st.text_input("API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
        
        if not st.session_state.cached_openai_models and key:
            st.session_state.cached_openai_models = get_openai_models(key)
            
        model_options = st.session_state.cached_openai_models if st.session_state.cached_openai_models else ["gpt-4o-mini", "o4-mini"]
        model_name = st.selectbox("Modelo", model_options)
        base_adapter = OpenAIAdapter(api_key=key, model=model_name)
    else:
        if not st.session_state.cached_ollama_models:
            st.session_state.cached_ollama_models = get_ollama_models()
            
        model_name = st.selectbox("Modelo Local", st.session_state.cached_ollama_models)
        base_adapter = OllamaAdapter(model=model_name)

    intervalo = st.number_input("Intervalo entre análises (minutos)", min_value=1, max_value=60, value=2)
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        # CORREÇÃO: Removido parâmetro depreciado do botão
        if st.button("▶️ Iniciar"):
            st.session_state.loop_active = True
            st.session_state.next_scan_timestamp = 0.0
    with col_btn2:
        # CORREÇÃO: Removido parâmetro depreciado do botão
        if st.button("⏹️ Parar"):
            st.session_state.loop_active = False

    status_cor = "green" if st.session_state.loop_active else "red"
    st.markdown(f"Status: <span style='color:{status_cor}; font-weight:bold;'>{'EXECUTANDO' if st.session_state.loop_active else 'PARADO'}</span>", unsafe_allow_html=True)
    st.caption(f"Última Varredura: {st.session_state.last_scan}")

# 3. Preparação das ferramentas base da Infraestrutura
k8s = K8sServiceAdapter()
checker = K8sHealthChecker()
adapter = LLMMonitorDecorator(base_adapter, provider_choice, st.session_state.calmsea_collector)

# --- TEMPLATE PRINCIPAL / DASHBOARD ---
st.title("CalmSea Dashboard")
st.markdown("---")

@st.fragment
def render_monitoring_panel():
    st.write(f"⏱ *Última verificação interna às: {datetime.now().strftime('%H:%M:%S')}*")
    
    namespaces_reais = k8s.list_namespaces()
    if not namespaces_reais:
        namespaces_reais = ["default"]
        
    scores_dict = {}
    all_pods_accumulated = []
    
    for ns in namespaces_reais:
        score_ns, pods_ns, trigger_ns, msg_ns = scan_namespace_health(k8s, ns)
        scores_dict[ns] = {
            "score": score_ns,
            "trigger": trigger_ns,
            "message": msg_ns,
            "pods_lista": pods_ns
        }
        all_pods_accumulated.extend(pods_ns)
        
    score_cluster = int(sum(item["score"] for item in scores_dict.values()) / len(scores_dict))

    # CORREÇÃO: Substituído use_container_width por width="stretch" no container principal
    with st.container(border=True):
        st.markdown("### 📊 Cluster Global Status")
        st.plotly_chart(
            create_phantom_gauge("", score_cluster), 
            selection_mode="none", 
            width="stretch",
            key="gauge_global_cluster"
        )
    
    st.markdown("#### 📊 Distribuição por Namespaces Ativos")
    
    MAX_COLS = 3
    namespaces_lista = list(namespaces_reais)
    
    for i in range(0, len(namespaces_lista), MAX_COLS):
        grupo_ns = namespaces_lista[i:i + MAX_COLS]
        cols_namespaces = st.columns(len(grupo_ns)) 
        
        for idx, ns in enumerate(grupo_ns):
            with cols_namespaces[idx]:
                with st.container(border=True):
                    st.markdown(f"📦 **NS: {ns}**")
                    # CORREÇÃO: Substituído use_container_width por width="stretch"
                    st.plotly_chart(
                        create_phantom_gauge("", scores_dict[ns]["score"]), 
                        selection_mode="none",
                        width="stretch",
                        key=f"gauge_ns_{ns}"
                    )

    st.markdown("### 📋 Mapeamento de Workloads Ativos")
    if all_pods_accumulated:
        df_pods = pd.DataFrame(all_pods_accumulated)
        # CORREÇÃO: st.dataframe expande por padrão na versão nova, parâmetro removido/limpo
        st.dataframe(df_pods, hide_index=True)
    else:
        st.info("Nenhum workload ativo mapeado nos namespaces monitorados.")

    # --- SOBERANIA OPERACIONAL: CIRCUITO DE AUTO-REMEDIAÇÃO DINÂMICO COM WATCHDOG PROTOCOL ---
    if st.session_state.loop_active:
        if time.time() >= st.session_state.next_scan_timestamp:
            
            for ns in namespaces_reais:
                if scores_dict[ns]["trigger"]:
                    msg_erro = scores_dict[ns]["message"]
                    
                    pods_do_namespace = scores_dict[ns]["pods_lista"]
                    pod_afetado = next((p["Pod"] for p in pods_do_namespace if "❌" in p["Health"]), None)
                    
                    if not pod_afetado:
                        continue
                        
                    st.toast(f"🚨 Anomalia em '{ns}' no Pod '{pod_afetado}'! Despertando AgentK...", icon="⚠️")
                    
                    spec_original = {}
                    try:
                        raw_pod = k8s.read_resource(resource_type="pod", name=pod_afetado, namespace=ns)
                        if raw_pod and "error" not in raw_pod:
                            spec_original = {
                                "metadata": {
                                    "name": raw_pod.get("metadata", {}).get("name"),
                                    "labels": raw_pod.get("metadata", {}).get("labels", {})
                                },
                                "spec": raw_pod.get("spec", {})
                            }
                    except Exception:
                        pass

                    spec_str = json.dumps(spec_original, indent=2) if spec_original else "Não foi possível extrair a Spec original."

                    agent_dinamico = AgentService(
                        llm_provider=adapter, 
                        k8s_adapter=k8s, 
                        health_checker=checker, 
                        target_namespace=ns,
                        early_healthcheck_timeout=25
                    )
                    
                    with st.spinner(f"AgentK aplicando engenharia de correção em '{ns}' para o pod '{pod_afetado}'..."):
                        agent_dinamico.run(user_prompt=(
                            f"Anomalia crítica detectada no namespace '{ns}' para o recurso Pod '{pod_afetado}'.\n"
                            f"Telemetria do Erro: {msg_erro}\n"
                            f"Especificação Atual no Cluster (JSON): \n{spec_str}\n\n"
                            f"ESTRATÉGIA RIGOROSA DE AUTO-REMEDIAÇÃO (PROTOCOLO DE SOBERANIA):\n"
                            f"1. [RESOLUÇÃO] Se o Pod '{pod_afetado}' ainda existir, execute IMEDIATAMENTE a ferramenta `delete_resource` para removê-lo.\n"
                            f"2. [CONSTRUÇÃO] Após o delete retornar SUCCESS, crie um novo manifesto YAML mantendo rigorosamente 'kind: Pod', o nome 'name: {pod_afetado}' e o namespace '{ns}'.\n"
                            f"3. [INTEGRIDADE] Mantenha o nome do container interno idêntico ao metadado original fornecido no JSON para evitar erros de imutabilidade. Altere APENAS a tag da imagem para uma versão estável oficial (ex: 'nginx:latest').\n"
                            f"4. [REMEDIAÇÃO] Execute a ferramenta `apply_manifest` uma única vez para subir o recurso corrigido.\n"
                            f"5. [SINAL DE PARADA OBRIGATÓRIO] Assim que a ferramenta `apply_manifest` retornar status 'SUCCESS' (recurso criado), você cumpriu sua missão. É EXPRESSAMENTE PROIBIDO tentar aplicar novos manifestos por cima na próxima iteração ou deletar o pod novamente. O motor de automação em Python cuidará do HealthCheck ativo. Encerre imediatamente o fluxo."
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