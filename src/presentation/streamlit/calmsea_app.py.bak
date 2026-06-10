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

st.set_page_config(page_title="CalmSea", page_icon="🌊", layout="wide")

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
# === SUBSTITUA EXCLUSIVAMENTE A FUNÇÃO SCAN_NAMESPACE_HEALTH POR ESTA ===

def scan_namespace_health(k8s_adapter, ns):
    """Varre o namespace aplicando a estratégia simplificada de White-listing de Saúde."""
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
            container_states = diag.get("container_states", [])
            
    # --- CRITÉRIO CIRÚRGICO DE SAÚDE (WHITE-LIST) ---
            # 1. A fase precisa ser obrigatoriamente Running
            phase_ok = (phase == "Running")
            
            # 2. Todos os containers precisam estar Ready=True, sem estarem travados em Waiting e com ZERO restarts
            containers_ok = True
            falha_detectada = "Instável"
            
            if container_states:
                for c in container_states:
                    # Se o container não está pronto OU se ele já sofreu algum restart mecânico
                    if not c.get("ready", False):
                        containers_ok = False
                        falha_detectada = c.get("reason") or "ContainerNotReady"
                        break
                    elif c.get("restart_count", 0) > 0:
                        containers_ok = False
                        falha_detectada = "CrashLoop/ProbeFailure"
                        break
            else:
                containers_ok = False
            
            # 3. Não pode haver histórico latente de falha de sonda nos eventos
            has_probe_failure = any("probe" in str(iss.get("message", "")).lower() for iss in issues)
            if has_probe_failure:
                falha_detectada = "ProbeFailure"

            # --- VALIDAÇÃO FINAL ---
            if phase_ok and containers_ok and not has_probe_failure:
                status_text = "✅ Healthy"
            else:
                unhealthy_pods += 1
                remediation_trigger = True
                status_text = f"❌ Unhealthy ({falha_detectada})"
                critical_msg = f"Desvio detectado no estado esperado do Pod: {falha_detectada}"               
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
        # CORREÇÃO LOGS CHATOS: Removido use_container_width do logo
        st.image(logo_path)
    else:
        st.info("🌊 CalmSea")

    st.title("⚙️ Configuração")
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
        if st.button("▶️ Iniciar"):
            st.session_state.loop_active = True
            st.session_state.next_scan_timestamp = 0.0
    with col_btn2:
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
                    st.plotly_chart(
                        create_phantom_gauge("", scores_dict[ns]["score"]), 
                        selection_mode="none",
                        width="stretch",
                        key=f"gauge_ns_{ns}"
                    )

    st.markdown("### 📋 Mapeamento de Workloads Ativos")
    if all_pods_accumulated:
        df_pods = pd.DataFrame(all_pods_accumulated)
        st.dataframe(df_pods, hide_index=True)
    else:
        st.info("Nenhum workload ativo mapeado nos namespaces monitorados.")

    # --- SOBERANIA OPERACIONAL: CIRCUITO DE AUTO-REMEDIAÇÃO CORRIGIDO ---
    if st.session_state.loop_active:
        if time.time() >= st.session_state.next_scan_timestamp:
            
            necessita_rerun = False
            
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
                            f"AMBIENTE: Namespace '{ns}' | Pod com problema: '{pod_afetado}'\n"
                            f"TEXTO DO ERRO: {msg_erro}\n"
                            f"JSON ORIGINAL DO POD:\n{spec_str}\n\n"
                            f"ESTRATÉGIA OBRIGATÓRIA:\n"
                            f"1. Use as ferramentas disponíveis para extrair o estado real do cluster no namespace '{ns}'. Se necessário, liste os recursos primeiro e busque detalhes/logs apenas dos suspeitos.\n"
                            f"2. Execute obrigatoriamente a ferramenta `get_pod_diagnostics` para qualquer Pod que esteja em estado Pending, ContainerCreating, FailedMount, ImagePullBackOff, ErrImagePull, CrashLoopBackOff, Error ou CreateContainerConfigError para validar a causa-raiz estrutural antes de aplicar alterações.\n\n"
                            f"SIGA EXATAMENTE ESTES 3 PASSOS EM SEQUÊNCIA (PROIBIDO TEXTO LIVRE OU PEDIR DADOS):\n"
                            f"Passo 1: [DELETAR] Chame a ferramenta `delete_resource` para apagar o Pod '{pod_afetado}' do namespace '{ns}'. É obrigatório apagar o Pod antes de tentar criar um novo, porque Pods não aceitam atualizações diretas de configuração enquanto estão vivos.\n"
                            f"Passo 2: [CORRIGIR E APLICAR] Na iteração seguinte, use a ferramenta `apply_manifest`. Monte o YAML do Pod usando o mesmo nome '{pod_afetado}'. Mantenha as portas, variáveis e volumes do JSON original, mas corrija o campo que causou o erro\n"
                            f"Passo 3: [REGRA DE PARADA] Assim que a ferramenta `apply_manifest` retornar sucesso ('created'), use a ação `reply` apenas para avisar que terminou e finalize o programa imediatamente."
                ))
                        
                    st.toast(f"📦 Recurso recriado em '{ns}'! Aguardando estabilização do container...", icon="⏳")
                    necessita_rerun = True

            if necessita_rerun:
                time.sleep(5) # Aumentado para 5 segundos para garantir transição completa do Minikube
                st.toast("✅ Todos os ambientes afetados foram estabilizados!", icon="⚓")
                st.session_state.next_scan_timestamp = time.time() + (intervalo * 60)
                st.rerun()

            st.session_state.next_scan_timestamp = time.time() + (intervalo * 60)

render_monitoring_panel()

# --- 4. ORQUESTRADOR DE ALTA FREQUÊNCIA (HEARTBEAT LOOP) ---
if st.session_state.loop_active:
    time.sleep(1)
    st.session_state.last_scan = datetime.now().strftime("%H:%M:%S")
    st.rerun()