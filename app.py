"""
Autonomous Research Agent - Streamlit UI
A premium, dark-themed dashboard for conducting AI-powered academic research.
"""

import sys
import time
import json
import threading
from pathlib import Path
from datetime import datetime

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent))

from src.pipeline import run_research_pipeline, PIPELINE_STEPS
from src.config import OUTPUT_DIR

# ─── Thread-safe shared state ─────────────────────────────────────────────────
# st.session_state CANNOT be accessed from background threads.
# We use this plain dict for thread → main-loop communication instead.
# IMPORTANT: Must use @st.cache_resource so it is NOT reset on every Streamlit
# rerun (app.py is re-executed from top on every user interaction).
@st.cache_resource
def _get_shared():
    return {
        "completed_steps": [],
        "current_step": None,
        "progress": 0.0,
        "logs": [],
        "research_state": None,
        "is_running": False,
    }, threading.Lock()

_thread_shared, _thread_lock = _get_shared()

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AutoReAgent | Autonomous Research Agent",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #0a0e1a 0%, #0d1225 50%, #0a0e1a 100%);
    min-height: 100vh;
}

/* ── Hero Header ── */
.hero-header {
    background: linear-gradient(135deg, #1a1f3a 0%, #0f1729 100%);
    border: 1px solid rgba(99, 102, 241, 0.3);
    border-radius: 20px;
    padding: 2rem 2.5rem;
    margin-bottom: 2rem;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.hero-header::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(ellipse at center, rgba(99, 102, 241, 0.08) 0%, transparent 60%);
    animation: pulse-glow 4s ease-in-out infinite;
}
@keyframes pulse-glow {
    0%, 100% { opacity: 0.5; }
    50% { opacity: 1; }
}
.hero-title {
    font-size: 2.8rem;
    font-weight: 800;
    background: linear-gradient(135deg, #818cf8, #6366f1, #a5b4fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0.5rem 0;
}
.hero-subtitle {
    color: #94a3b8;
    font-size: 1.1rem;
    font-weight: 400;
    margin-top: 0.5rem;
}

/* ── Status Cards ── */
.status-card {
    background: linear-gradient(135deg, #1e2340 0%, #1a1f35 100%);
    border: 1px solid rgba(99, 102, 241, 0.2);
    border-radius: 16px;
    padding: 1.2rem 1.5rem;
    margin: 0.4rem 0;
    transition: all 0.3s ease;
}
.status-card.active {
    border-color: #6366f1;
    background: linear-gradient(135deg, #1e1f4a 0%, #1a1f35 100%);
    box-shadow: 0 0 20px rgba(99, 102, 241, 0.2);
}
.status-card.done {
    border-color: rgba(52, 211, 153, 0.4);
    background: linear-gradient(135deg, #0f2a1e 0%, #1a1f35 100%);
}
.status-card.error {
    border-color: rgba(239, 68, 68, 0.4);
    background: linear-gradient(135deg, #2a0f0f 0%, #1a1f35 100%);
}

/* ── Metric Cards ── */
.metric-card {
    background: linear-gradient(135deg, #1e2340, #161b2f);
    border: 1px solid rgba(99, 102, 241, 0.25);
    border-radius: 14px;
    padding: 1.2rem;
    text-align: center;
    transition: transform 0.2s ease;
}
.metric-card:hover {
    transform: translateY(-2px);
    border-color: rgba(99, 102, 241, 0.5);
}
.metric-value {
    font-size: 2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #818cf8, #a5b4fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.metric-label {
    color: #64748b;
    font-size: 0.8rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 0.3rem;
}

/* ── Report Container ── */
.report-container {
    background: linear-gradient(135deg, #12172b, #0f1422);
    border: 1px solid rgba(99, 102, 241, 0.2);
    border-radius: 16px;
    padding: 2rem;
    font-family: 'Inter', sans-serif;
    line-height: 1.8;
    color: #e2e8f0;
}

/* ── Paper Card ── */
.paper-card {
    background: linear-gradient(135deg, #1a2035, #151929);
    border: 1px solid rgba(99, 102, 241, 0.15);
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    margin: 0.6rem 0;
    transition: all 0.2s ease;
}
.paper-card:hover {
    border-color: rgba(99, 102, 241, 0.4);
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}
.paper-title {
    font-weight: 600;
    color: #a5b4fc;
    font-size: 0.95rem;
}
.paper-meta {
    color: #64748b;
    font-size: 0.8rem;
    margin-top: 0.3rem;
}
.relevance-badge {
    display: inline-block;
    padding: 0.15rem 0.6rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
}
.relevance-high { background: rgba(52,211,153,0.15); color: #34d399; }
.relevance-med  { background: rgba(251,191,36,0.15);  color: #fbbf24; }
.relevance-low  { background: rgba(239,68,68,0.15);   color: #ef4444; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1225, #0a0e1a);
    border-right: 1px solid rgba(99, 102, 241, 0.15);
}

/* ── Sidebar widget labels ── */
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stSlider label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] .stMarkdown p {
    color: #c4c9e2 !important;
    font-weight: 500 !important;
}

/* Make sidebar bold headings (Configuration, Pipeline Steps, Past Reports) pop */
[data-testid="stSidebar"] strong {
    color: #a5b4fc !important;
    font-weight: 700 !important;
}

/* Sidebar selectbox / dropdown text */
[data-testid="stSidebar"] .stSelectbox > div > div {
    color: #e2e8f0 !important;
    background: #1a1f35 !important;
    border-color: rgba(99, 102, 241, 0.35) !important;
}

/* Main area widget labels */
.stTextArea label, .stTextInput label, .stSlider label, .stSelectbox label {
    color: #c4c9e2 !important;
    font-weight: 500 !important;
}

/* ── Example Questions heading gradient ── */
.example-heading {
    font-size: 1.1rem;
    font-weight: 700;
    background: linear-gradient(135deg, #4f46e5, #818cf8, #a5b4fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.6rem;
    display: inline-block;
}

/* ── All Buttons base ── */
.stButton > button {
    background: linear-gradient(135deg, #4f46e5, #6366f1);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 0.7rem 2rem;
    font-weight: 600;
    font-family: 'Inter', sans-serif;
    font-size: 1rem;
    transition: all 0.3s ease;
    box-shadow: 0 4px 20px rgba(99, 102, 241, 0.35);
}
.stButton > button:hover {
    background: linear-gradient(135deg, #4338ca, #4f46e5);
    box-shadow: 0 6px 25px rgba(99, 102, 241, 0.5);
    transform: translateY(-1px);
}

/* ── Example Question Buttons (type=primary) — same gradient as Start Pipeline ── */
button[data-testid="baseButton-primary"],
button[data-testid="baseButton-primary"]:focus,
button[data-testid="baseButton-primary"]:active {
    background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%) !important;
    background-color: #6366f1 !important;
    color: #ffffff !important;
    border: none !important;
    border-color: transparent !important;
    border-radius: 10px !important;
    font-size: 0.83rem !important;
    font-weight: 600 !important;
    padding: 0.55rem 1rem !important;
    box-shadow: 0 3px 14px rgba(99, 102, 241, 0.45) !important;
    transition: all 0.25s ease !important;
}
button[data-testid="baseButton-primary"]:hover {
    background: linear-gradient(135deg, #4338ca 0%, #4f46e5 100%) !important;
    background-color: #4f46e5 !important;
    box-shadow: 0 6px 22px rgba(99, 102, 241, 0.65) !important;
    transform: translateY(-2px) !important;
    color: #ffffff !important;
    border: none !important;
}
button[data-testid="baseButton-primary"]:disabled,
button[data-testid="baseButton-primary"][disabled] {
    background: linear-gradient(135deg, #2d2b6e, #3b3f8a) !important;
    background-color: #2d2b6e !important;
    opacity: 0.55 !important;
    box-shadow: none !important;
    transform: none !important;
}

/* ── Input Fields ── */
.stTextArea > div > textarea, .stTextInput > div > input {
    background: #1a1f35 !important;
    border: 1px solid rgba(99, 102, 241, 0.3) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    font-family: 'Inter', sans-serif !important;
}
.stTextArea > div > textarea:focus, .stTextInput > div > input:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15) !important;
}

/* ── Progress Bar ── */
.stProgress > div > div > div {
    background: linear-gradient(90deg, #6366f1, #818cf8) !important;
    border-radius: 999px !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #1a1f35;
    border-radius: 12px;
    padding: 0.3rem;
    gap: 0.3rem;
    border: 1px solid rgba(99, 102, 241, 0.15);
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    border-radius: 8px;
    color: #64748b;
    font-weight: 500;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #4f46e5, #6366f1) !important;
    color: white !important;
}

/* ── Divider ── */
hr {
    border-color: rgba(99, 102, 241, 0.15) !important;
    margin: 1.5rem 0 !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0a0e1a; }
::-webkit-scrollbar-thumb { background: #4f46e5; border-radius: 3px; }

/* ── Code ── */
code {
    font-family: 'JetBrains Mono', monospace !important;
    background: rgba(99, 102, 241, 0.1) !important;
    color: #a5b4fc !important;
    border-radius: 4px;
}

/* ── Agent Step Pills ── */
.step-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.4rem 0.9rem;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 600;
    margin: 0.2rem;
}
.step-done    { background: rgba(52,211,153,0.15); color: #34d399; border: 1px solid rgba(52,211,153,0.3); }
.step-active  { background: rgba(99,102,241,0.2);  color: #818cf8; border: 1px solid rgba(99,102,241,0.5); }
.step-pending { background: rgba(30,35,64,0.5);    color: #475569; border: 1px solid rgba(71,85,105,0.3); }

/* ── Alert boxes ── */
.alert-warning {
    background: rgba(251, 191, 36, 0.08);
    border: 1px solid rgba(251, 191, 36, 0.25);
    border-radius: 10px;
    padding: 0.8rem 1.2rem;
    color: #fbbf24;
    font-size: 0.9rem;
    margin: 0.5rem 0;
}
.alert-success {
    background: rgba(52, 211, 153, 0.08);
    border: 1px solid rgba(52, 211, 153, 0.25);
    border-radius: 10px;
    padding: 0.8rem 1.2rem;
    color: #34d399;
    font-size: 0.9rem;
    margin: 0.5rem 0;
}
.alert-error {
    background: rgba(239, 68, 68, 0.08);
    border: 1px solid rgba(239, 68, 68, 0.25);
    border-radius: 10px;
    padding: 0.8rem 1.2rem;
    color: #f87171;
    font-size: 0.9rem;
    margin: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)


# ─── Session State Init ────────────────────────────────────────────────────────
def init_session():
    defaults = {
        "research_state": None,
        "is_running": False,
        "completed_steps": [],
        "current_step": None,
        "progress": 0.0,
        "logs": [],
        "start_time": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_session()


def sync_thread_state():
    """Copy _thread_shared into st.session_state (main thread only)."""
    with _thread_lock:
        st.session_state.completed_steps = list(_thread_shared["completed_steps"])
        st.session_state.current_step = _thread_shared["current_step"]
        st.session_state.progress = _thread_shared["progress"]
        st.session_state.logs = list(_thread_shared["logs"])
        st.session_state.is_running = _thread_shared["is_running"]
        if _thread_shared["research_state"] is not None:
            st.session_state.research_state = _thread_shared["research_state"]
            _thread_shared["research_state"] = None  # consume once


# Sync on every rerun if a pipeline was started
if _thread_shared["is_running"] or st.session_state.is_running:
    sync_thread_state()


# ─── Helpers ──────────────────────────────────────────────────────────────────

def get_step_status(step_name: str) -> str:
    if step_name in st.session_state.completed_steps:
        return "done"
    if step_name == st.session_state.current_step:
        return "active"
    return "pending"


def get_step_icon(status: str) -> str:
    return {"done": "✅", "active": "⚡", "pending": "○"}[status]


def format_elapsed(start: float) -> str:
    elapsed = time.time() - start
    m, s = divmod(int(elapsed), 60)
    return f"{m:02d}:{s:02d}"


def render_relevance_badge(score: float) -> str:
    if score >= 0.75:
        cls = "relevance-high"
        label = f"High {score:.0%}"
    elif score >= 0.5:
        cls = "relevance-med"
        label = f"Med {score:.0%}"
    else:
        cls = "relevance-low"
        label = f"Low {score:.0%}"
    return f'<span class="relevance-badge {cls}">{label}</span>'


def build_confidence_gauge(score: float):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score * 100,
        domain={"x": [0, 1], "y": [0, 1]},
        number={"suffix": "%", "font": {"size": 36, "color": "#818cf8"}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#475569", "dtick": 25,
                     "tickfont": {"color": "#64748b", "size": 11}},
            "bar": {"color": "#6366f1", "thickness": 0.25},
            "bgcolor": "#1a1f35",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 40], "color": "rgba(239,68,68,0.15)"},
                {"range": [40, 70], "color": "rgba(251,191,36,0.15)"},
                {"range": [70, 100], "color": "rgba(52,211,153,0.15)"},
            ],
            "threshold": {
                "line": {"color": "#a5b4fc", "width": 2},
                "thickness": 0.75,
                "value": score * 100,
            },
        },
        title={"text": "Research Confidence", "font": {"size": 14, "color": "#94a3b8"}},
    ))
    fig.update_layout(
        height=220,
        margin=dict(l=20, r=20, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter"},
    )
    return fig


def build_relevance_chart(papers):
    if not papers:
        return None
    titles = [p.title[:35] + "..." if len(p.title) > 35 else p.title for p in papers]
    scores = [p.relevance_score for p in papers]
    colors = ["#34d399" if s >= 0.75 else "#fbbf24" if s >= 0.5 else "#f87171" for s in scores]

    fig = go.Figure(go.Bar(
        x=scores,
        y=titles,
        orientation="h",
        marker_color=colors,
        marker_line_width=0,
        text=[f"{s:.0%}" for s in scores],
        textposition="outside",
        textfont={"color": "#94a3b8", "size": 11},
    ))
    fig.update_layout(
        height=max(250, len(papers) * 32),
        margin=dict(l=10, r=60, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(range=[0, 1.1], showgrid=True, gridcolor="rgba(99,102,241,0.1)",
                   tickformat=".0%", tickfont={"color": "#64748b"}),
        yaxis=dict(showgrid=False, tickfont={"color": "#94a3b8", "size": 11}),
        showlegend=False,
    )
    return fig


def build_citation_graph_viz(state):
    """Build an interactive citation graph using plotly."""
    if not state or not state.citation_edges:
        return None

    try:
        import networkx as nx
        G = nx.DiGraph()

        paper_map = {p.paper_id: p for p in state.filtered_papers}
        for p in state.filtered_papers:
            G.add_node(p.paper_id, title=p.title[:40], year=p.year or 0)

        for e in state.citation_edges:
            G.add_edge(e["source"], e["target"])

        pos = nx.spring_layout(G, seed=42, k=1.5)

        edge_x, edge_y = [], []
        for u, v in G.edges():
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            edge_x += [x0, x1, None]
            edge_y += [y0, y1, None]

        node_x = [pos[n][0] for n in G.nodes()]
        node_y = [pos[n][1] for n in G.nodes()]
        node_text = [G.nodes[n]["title"] for n in G.nodes()]
        node_sizes = [20 + G.in_degree(n) * 10 for n in G.nodes()]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=edge_x, y=edge_y, mode="lines",
            line=dict(width=1, color="rgba(99,102,241,0.3)"),
            hoverinfo="none"
        ))
        fig.add_trace(go.Scatter(
            x=node_x, y=node_y, mode="markers+text",
            marker=dict(size=node_sizes, color="#6366f1", line=dict(width=2, color="#818cf8")),
            text=node_text,
            textposition="top center",
            textfont=dict(color="#94a3b8", size=10),
            hovertemplate="%{text}<extra></extra>",
        ))
        fig.update_layout(
            showlegend=False,
            height=400,
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        )
        return fig
    except Exception:
        return None


# ─── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 1rem 0 0.5rem;">
        <div style="font-size:2.5rem;">🔬</div>
        <div style="font-size:1.1rem; font-weight:700; color:#818cf8;">AutoReAgent</div>
        <div style="font-size:0.75rem; color:#475569; margin-top:0.2rem;">Autonomous Research Agent</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    st.markdown(
        '<div style="font-size:0.95rem;font-weight:700;color:#a5b4fc;letter-spacing:0.02em;margin-bottom:0.3rem;">⚙️ Configuration</div>',
        unsafe_allow_html=True
    )

    ollama_model = st.selectbox(
        "🤖 LLM Model",
        ["llama3", "llama3.2", "mistral", "mixtral", "deepseek-coder", "llama3.1"],
        help="Select the Ollama model to use",
        index=0,
        key="ollama_model_select"
    )

    max_papers = st.slider("📄 Max Papers to Process", 3, 20, 8, help="Papers to fetch and analyze")
    relevance_thresh = st.slider("🎯 Relevance Threshold", 0.3, 0.9, 0.6, 0.05,
                                  help="Minimum score to include a paper")

    st.divider()
    st.markdown(
        '<div style="font-size:0.95rem;font-weight:700;color:#a5b4fc;letter-spacing:0.02em;margin-bottom:0.3rem;">🗂️ Pipeline Steps</div>',
        unsafe_allow_html=True
    )

    for step_id, step_label in PIPELINE_STEPS:
        status = get_step_status(step_id)
        icon = get_step_icon(status)
        color_map = {"done": "#34d399", "active": "#818cf8", "pending": "#475569"}
        color = color_map[status]
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:0.5rem;'
            f'padding:0.3rem 0;color:{color};font-size:0.85rem;">'
            f'<span>{icon}</span><span>{step_label}</span></div>',
            unsafe_allow_html=True
        )

    if st.session_state.is_running and st.session_state.start_time:
        st.divider()
        st.markdown(
            f'<div style="text-align:center;color:#64748b;font-size:0.8rem;">'
            f'⏱️ Elapsed: {format_elapsed(st.session_state.start_time)}</div>',
            unsafe_allow_html=True
        )

    # Past reports
    st.divider()
    st.markdown(
        '<div style="font-size:0.95rem;font-weight:700;color:#a5b4fc;letter-spacing:0.02em;margin-bottom:0.3rem;">📁 Past Reports</div>',
        unsafe_allow_html=True
    )

    # ── Handle pending delete (do before rendering so list refreshes) ──
    _to_delete = st.session_state.pop("_confirm_delete", None)
    if _to_delete:
        from pathlib import Path as _P
        _del_path = _P(_to_delete)
        if _del_path.exists():
            _del_path.unlink()
        # Clear from view if it was open
        st.session_state.pop("load_report", None)
        st.rerun()

    report_files = sorted(OUTPUT_DIR.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)[:5]

    if not report_files:
        st.markdown(
            '<div style="color:#475569;font-size:0.78rem;padding:0.3rem 0;">No reports yet.</div>',
            unsafe_allow_html=True
        )

    for rf in report_files:
        col_open, col_del = st.columns([5, 1])
        with col_open:
            if st.button(
                f"📄 {rf.stem[:22]}…",
                key=f"report_open_{rf.name}",
                use_container_width=True,
                help=rf.stem
            ):
                st.session_state["load_report"] = rf.read_text(encoding="utf-8")
                st.rerun()
        with col_del:
            if st.button(
                "🗑️",
                key=f"report_del_{rf.name}",
                help=f"Delete {rf.name}",
                use_container_width=True,
            ):
                st.session_state["_confirm_delete"] = str(rf)
                st.rerun()


# ─── Main Layout ─────────────────────────────────────────────────────────────

st.markdown("""
<div class="hero-header">
    <div style="font-size:1rem;color:#6366f1;font-weight:600;letter-spacing:0.1em;">
        🔬 AUTONOMOUS MULTI-AGENT SYSTEM
    </div>
    <div class="hero-title">Research Agent</div>
    <div class="hero-subtitle">
        Plan → Search → Filter → Extract → Compare → Debate → Report
    </div>
</div>
""", unsafe_allow_html=True)

# ─── Input Section ────────────────────────────────────────────────────────────

col_input, col_examples = st.columns([3, 2])

with col_input:
    st.markdown("### 🎯 Research Question")
    # Consume any staged example question BEFORE the widget is instantiated
    _default_q = st.session_state.pop("_example_q", "") or ""
    research_question = st.text_area(
        "Enter your research question",
        value=_default_q,
        placeholder="e.g. What are the latest advancements in diffusion-based video generation models?",
        height=100,
        key="research_q",
        label_visibility="collapsed"
    )

with col_examples:
    st.markdown(
        '<div class="example-heading">💡 Example Questions — click to run instantly</div>',
        unsafe_allow_html=True
    )
    examples = [
        "What are the latest advancements in diffusion-based video generation?",
        "How do large language models handle multi-step reasoning?",
        "What are the state-of-the-art methods for 3D neural scene reconstruction?",
        "Survey of reinforcement learning from human feedback (RLHF) methods",
    ]
    for ex in examples:
        if st.button(
            f"⚡ {ex[:55]}...",
            key=f"ex_{ex[:20]}",
            type="primary",
            use_container_width=True,
            disabled=st.session_state.is_running,
            help="Click to instantly run this research question"
        ):
            st.session_state["_example_q"] = ex
            st.session_state["_auto_run"] = True
            st.rerun()

st.divider()

# ─── Run Button ───────────────────────────────────────────────────────────────

# Consume auto-run flag BEFORE rendering button (set by example question clicks)
_auto_run = st.session_state.pop("_auto_run", False)

# If example click triggered auto-run, use that question; otherwise use text area value
_effective_question = _default_q if (_auto_run and _default_q) else research_question

can_run = bool(_effective_question and _effective_question.strip() and not st.session_state.is_running)

run_col, _, info_col = st.columns([2, 1, 3])
with run_col:
    run_clicked = st.button(
        "🚀 Start Research Pipeline",
        disabled=not can_run,
        use_container_width=True,
        key="run_btn"
    )
with info_col:
    if st.session_state.is_running:
        st.markdown(
            '<div style="padding:0.6rem 0;color:#818cf8;font-size:0.85rem;">'
            '⏳ Pipeline is running… results will appear below.</div>',
            unsafe_allow_html=True
        )
    elif not _effective_question:
        st.markdown(
            '<div style="padding:0.6rem 0;color:#475569;font-size:0.85rem;">'
            '← Type a question or click an example to start.</div>',
            unsafe_allow_html=True
        )

# ─── Pipeline Execution ────────────────────────────────────────────────────────

if (run_clicked or _auto_run) and can_run:

    # Update config from sidebar
    import src.config as cfg
    cfg.MAX_PAPERS_PER_SEARCH = max_papers
    cfg.MAX_PAPERS_TO_PROCESS = max_papers
    cfg.RELEVANCE_THRESHOLD = relevance_thresh
    cfg.OLLAMA_MODEL = ollama_model

    # Use effective question (covers both manual input and auto-run from example click)
    _run_question = _effective_question.strip()

    # Reset both session state AND the thread-shared dict
    st.session_state.start_time = time.time()
    with _thread_lock:
        _thread_shared["completed_steps"] = []
        _thread_shared["current_step"] = "planner"
        _thread_shared["progress"] = 0.0
        _thread_shared["logs"] = []
        _thread_shared["research_state"] = None
        _thread_shared["is_running"] = True
    sync_thread_state()

    # Capture question for thread closure (covers both example click and manual entry)
    _question_for_thread = _effective_question.strip()

    def progress_callback(node_name: str, state):
        """Called from background thread — only writes to _thread_shared, never st.session_state."""
        step_names = [s[0] for s in PIPELINE_STEPS]
        with _thread_lock:
            if node_name not in _thread_shared["completed_steps"]:
                _thread_shared["completed_steps"].append(node_name)
            done_count = len(_thread_shared["completed_steps"])
            _thread_shared["progress"] = done_count / len(PIPELINE_STEPS)
            _thread_shared["logs"].append(f"✅ Completed: {node_name}")
            current_idx = step_names.index(node_name) if node_name in step_names else -1
            if current_idx + 1 < len(step_names):
                _thread_shared["current_step"] = step_names[current_idx + 1]
            else:
                _thread_shared["current_step"] = None

    def run_pipeline_threaded():
        """Runs in background thread — all state goes into _thread_shared."""
        try:
            state = run_research_pipeline(
                research_question=_question_for_thread,
                callback=progress_callback
            )
            with _thread_lock:
                _thread_shared["research_state"] = state
                _thread_shared["progress"] = 1.0
                _thread_shared["current_step"] = None
        except Exception as e:
            with _thread_lock:
                _thread_shared["logs"].append(f"❌ Pipeline error: {str(e)}")
        finally:
            with _thread_lock:
                _thread_shared["is_running"] = False

    thread = threading.Thread(target=run_pipeline_threaded, daemon=True)
    thread.start()
    st.rerun()


# ─── Progress Section ─────────────────────────────────────────────────────────

if st.session_state.is_running:
    st.markdown("### ⚡ Pipeline Running...")
    progress_bar = st.progress(st.session_state.progress)

    step_html = ""
    for step_id, step_label in PIPELINE_STEPS:
        status = get_step_status(step_id)
        cls = f"step-{status}"
        icon = {"done": "✅", "active": "⚡", "pending": "·"}[status]
        step_html += f'<span class="step-pill {cls}">{icon} {step_label}</span>'

    st.markdown(f'<div style="margin: 0.5rem 0;">{step_html}</div>', unsafe_allow_html=True)

    if st.session_state.logs:
        with st.expander("📋 Live Logs", expanded=False):
            for log in st.session_state.logs[-20:]:
                st.markdown(f'<div style="font-family:JetBrains Mono,monospace;font-size:0.8rem;color:#64748b;padding:0.1rem 0;">{log}</div>', unsafe_allow_html=True)

    time.sleep(2)
    st.rerun()


# ─── Results Section ──────────────────────────────────────────────────────────

state = st.session_state.get("research_state")
load_report = st.session_state.get("load_report")

if state or load_report:
    st.divider()
    st.markdown("### 📊 Research Results")

    if state:
        # ── Metric Cards ──
        papers = state.filtered_papers
        raw_count = len(state.raw_papers)
        filtered_count = len(papers)
        pdf_count = sum(1 for p in papers if p.full_text and len(p.full_text) > 200)
        confidence = state.confidence_score

        m1, m2, m3, m4 = st.columns(4)
        for col, val, label, icon in [
            (m1, raw_count, "Papers Found", "🔍"),
            (m2, filtered_count, "Papers Selected", "✅"),
            (m3, pdf_count, "PDFs Extracted", "📄"),
            (m4, f"{confidence:.0%}", "Confidence", "🎯"),
        ]:
            col.markdown(
                f'<div class="metric-card">'
                f'<div style="font-size:1.5rem">{icon}</div>'
                f'<div class="metric-value">{val}</div>'
                f'<div class="metric-label">{label}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

        # ── Tabs ──
        tab_report, tab_papers, tab_analysis, tab_debate, tab_graph, tab_critic = st.tabs([
            "📑 Report", "📚 Papers", "📊 Analysis", "⚔️ Debate", "🕸️ Citation Graph", "🔍 Critic"
        ])

        # ── Report Tab ──
        with tab_report:
            if state.final_report:
                dl_col, _ = st.columns([1, 4])
                with dl_col:
                    st.download_button(
                        "⬇️ Download Report",
                        data=state.final_report,
                        file_name=f"research_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                        mime="text/markdown",
                        use_container_width=True,
                    )
                st.markdown(
                    f'<div class="report-container">{state.final_report}</div>',
                    unsafe_allow_html=True
                )
            else:
                st.info("No report generated yet.")

        # ── Papers Tab ──
        with tab_papers:
            if papers:
                st.markdown(f"**{len(papers)} papers selected from {raw_count} candidates**")

                # Relevance chart
                chart = build_relevance_chart(papers)
                if chart:
                    st.plotly_chart(chart, use_container_width=True, key="relevance_chart")

                # Paper cards
                for i, p in enumerate(papers):
                    authors_str = ", ".join(p.authors[:3]) + (" et al." if len(p.authors) > 3 else "")
                    badge = render_relevance_badge(p.relevance_score)
                    url_link = f'<a href="{p.url}" target="_blank" style="color:#6366f1;text-decoration:none;">🔗 View Paper</a>' if p.url else ""

                    with st.expander(f"**{i+1}. {p.title[:80]}...**" if len(p.title) > 80 else f"**{i+1}. {p.title}**"):
                        st.markdown(
                            f'<div class="paper-card">'
                            f'<div class="paper-title">{p.title}</div>'
                            f'<div class="paper-meta">🧑‍🔬 {authors_str} | 📅 {p.year or "N/A"} | '
                            f'📚 {p.citation_count} citations | {p.source}</div>'
                            f'<div style="margin-top:0.5rem;">{badge} {url_link}</div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )

                        col1, col2 = st.columns(2)
                        with col1:
                            if p.methodology:
                                st.markdown("**⚙️ Methodology**")
                                st.markdown(f'<div style="color:#94a3b8;font-size:0.85rem;">{p.methodology}</div>', unsafe_allow_html=True)
                            if p.dataset:
                                st.markdown("**📦 Dataset**")
                                st.markdown(f'<div style="color:#94a3b8;font-size:0.85rem;">{p.dataset}</div>', unsafe_allow_html=True)
                        with col2:
                            if p.results:
                                st.markdown("**📈 Results**")
                                st.markdown(f'<div style="color:#94a3b8;font-size:0.85rem;">{p.results}</div>', unsafe_allow_html=True)
                            if p.limitations:
                                st.markdown("**⚠️ Limitations**")
                                st.markdown(f'<div style="color:#94a3b8;font-size:0.85rem;">{p.limitations}</div>', unsafe_allow_html=True)

                        if p.abstract:
                            st.markdown("**📝 Abstract**")
                            st.markdown(f'<div style="color:#64748b;font-size:0.82rem;line-height:1.6;">{p.abstract[:500]}...</div>', unsafe_allow_html=True)
            else:
                st.info("No papers found or selected.")

        # ── Analysis Tab ──
        with tab_analysis:
            analysis = state.comparative_analysis
            if analysis:
                st.markdown("#### ⚙️ Methodology Comparison")
                st.markdown(f'<div style="color:#94a3b8;line-height:1.7;">{analysis.methodology_comparison or "_N/A_"}</div>', unsafe_allow_html=True)

                st.divider()
                st.markdown("#### 📦 Dataset Comparison")
                st.markdown(f'<div style="color:#94a3b8;line-height:1.7;">{analysis.dataset_comparison or "_N/A_"}</div>', unsafe_allow_html=True)

                st.divider()
                col_trends, col_limits = st.columns(2)
                with col_trends:
                    st.markdown("#### 📈 Innovation Trends")
                    for t in analysis.innovation_trends:
                        st.markdown(f'<div style="color:#34d399;font-size:0.9rem;padding:0.3rem 0;">▶ {t}</div>', unsafe_allow_html=True)

                with col_limits:
                    st.markdown("#### ⚠️ Recurring Limitations")
                    for l in analysis.recurring_limitations:
                        st.markdown(f'<div style="color:#f87171;font-size:0.9rem;padding:0.3rem 0;">▶ {l}</div>', unsafe_allow_html=True)

                if analysis.performance_ranking:
                    st.divider()
                    st.markdown("#### 🏆 Performance Ranking")
                    for item in analysis.performance_ranking:
                        rank = item.get("rank", "?")
                        paper = item.get("paper", "Unknown")
                        reason = item.get("reason", "")
                        medal = ["🥇", "🥈", "🥉"][int(rank)-1] if str(rank) in ["1", "2", "3"] else "📌"
                        st.markdown(
                            f'<div style="padding:0.5rem 0;border-bottom:1px solid rgba(99,102,241,0.1);">'
                            f'<span style="color:#818cf8;font-weight:600;">{medal} #{rank}</span> '
                            f'<span style="color:#e2e8f0;">{paper}</span><br>'
                            f'<span style="color:#64748b;font-size:0.85rem;">{reason}</span>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
            else:
                st.info("No comparative analysis available.")

        # ── Debate Tab ──
        with tab_debate:
            if state.optimistic_view or state.skeptical_view:
                col_opt, col_skep = st.columns(2)
                with col_opt:
                    st.markdown("""
                    <div style="color:#34d399;font-weight:700;font-size:1.1rem;margin-bottom:0.8rem;">
                        🔬 Optimistic Analyst
                    </div>""", unsafe_allow_html=True)
                    st.markdown(
                        f'<div style="background:rgba(52,211,153,0.05);border:1px solid rgba(52,211,153,0.2);'
                        f'border-radius:12px;padding:1rem;color:#94a3b8;font-size:0.88rem;line-height:1.7;">'
                        f'{state.optimistic_view or "Not generated"}</div>',
                        unsafe_allow_html=True
                    )

                with col_skep:
                    st.markdown("""
                    <div style="color:#f87171;font-weight:700;font-size:1.1rem;margin-bottom:0.8rem;">
                        🔍 Skeptical Reviewer
                    </div>""", unsafe_allow_html=True)
                    st.markdown(
                        f'<div style="background:rgba(239,68,68,0.05);border:1px solid rgba(239,68,68,0.2);'
                        f'border-radius:12px;padding:1rem;color:#94a3b8;font-size:0.88rem;line-height:1.7;">'
                        f'{state.skeptical_view or "Not generated"}</div>',
                        unsafe_allow_html=True
                    )

                if state.merged_perspective:
                    st.divider()
                    st.markdown("""
                    <div style="color:#818cf8;font-weight:700;font-size:1.1rem;margin-bottom:0.8rem;">
                        ⚖️ Balanced Synthesis
                    </div>""", unsafe_allow_html=True)
                    st.markdown(
                        f'<div style="background:rgba(99,102,241,0.05);border:1px solid rgba(99,102,241,0.2);'
                        f'border-radius:12px;padding:1rem;color:#e2e8f0;font-size:0.9rem;line-height:1.8;">'
                        f'{state.merged_perspective}</div>',
                        unsafe_allow_html=True
                    )
            else:
                st.info("Debate not yet generated.")

        # ── Citation Graph Tab ──
        with tab_graph:
            if state.citation_edges:
                graph_fig = build_citation_graph_viz(state)
                if graph_fig:
                    st.plotly_chart(graph_fig, use_container_width=True, key="citation_fig")
                st.markdown(f"**Found {len(state.citation_edges)} citation relationships among analyzed papers.**")
                for edge in state.citation_edges[:10]:
                    st.markdown(
                        f'<div style="font-size:0.85rem;color:#64748b;padding:0.2rem 0;">'
                        f'📄 <span style="color:#818cf8;">{edge["source_title"][:40]}...</span> '
                        f'→ cites → '
                        f'<span style="color:#a5b4fc;">{edge["target_title"][:40]}...</span>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
            else:
                st.info("No cross-citations detected among the analyzed papers.")

        # ── Critic Tab ──
        with tab_critic:
            critic = state.critic_report
            if critic:
                gauge_col, info_col = st.columns([1, 2])
                with gauge_col:
                    st.plotly_chart(
                        build_confidence_gauge(critic.overall_quality_score),
                        use_container_width=True,
                        key="critic_gauge"
                    )
                with info_col:
                    if critic.hallucination_detected:
                        st.markdown('<div class="alert-warning">⚠️ Potential hallucinations detected. Review unsupported claims carefully.</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="alert-success">✅ No major hallucinations detected by the Critic Agent.</div>', unsafe_allow_html=True)

                    if critic.unsupported_claims:
                        st.markdown("**⚠️ Unsupported Claims:**")
                        for c in critic.unsupported_claims:
                            st.markdown(f'<div style="color:#fbbf24;font-size:0.85rem;padding:0.2rem 0;">• {c}</div>', unsafe_allow_html=True)

                    if critic.suggestions_for_improvement:
                        st.markdown("**💡 Suggestions:**")
                        for s in critic.suggestions_for_improvement:
                            st.markdown(f'<div style="color:#94a3b8;font-size:0.85rem;padding:0.2rem 0;">• {s}</div>', unsafe_allow_html=True)
            else:
                st.info("Critic review not yet completed.")

    elif load_report:
        # Show a previously loaded report
        st.markdown(f'<div class="report-container">{load_report}</div>', unsafe_allow_html=True)
        dc, _ = st.columns([1, 4])
        with dc:
            st.download_button(
                "⬇️ Download",
                data=load_report,
                file_name="loaded_report.md",
                mime="text/markdown"
            )

# ─── Empty State ──────────────────────────────────────────────────────────────

elif not st.session_state.is_running:
    st.markdown("""
    <div style="text-align:center;padding:4rem 2rem;color:#475569;">
        <div style="font-size:4rem;margin-bottom:1rem;">🔬</div>
        <div style="font-size:1.3rem;font-weight:600;color:#64748b;margin-bottom:0.8rem;">
            Ready to Begin Research
        </div>
        <div style="font-size:0.95rem;max-width:500px;margin:0 auto;line-height:1.7;">
            Enter a research question above and click <strong style="color:#818cf8;">Start Research Pipeline</strong>.<br>
            The system will autonomously search, filter, extract, compare, and generate a structured report.
        </div>
    </div>
    """, unsafe_allow_html=True)

# ─── Error display ────────────────────────────────────────────────────────────

if state and state.errors:
    with st.expander("⚠️ Pipeline Errors", expanded=False):
        for err in state.errors:
            st.markdown(f'<div class="alert-error">⚠️ {err}</div>', unsafe_allow_html=True)
