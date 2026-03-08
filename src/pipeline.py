"""
LangGraph Pipeline
Orchestrates all agents in a stateful directed graph.
Supports streaming state updates for UI integration.
"""

from typing import Callable, Generator
from loguru import logger

try:
    from langgraph.graph import StateGraph, START, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False

from src.config import ResearchState
from src.agents.planner import run_planner_agent
from src.agents.search import run_search_agent
from src.agents.filter import run_filter_agent
from src.agents.pdf_reader import run_pdf_reader_agent
from src.agents.extractor import run_extractor_agent
from src.agents.comparison import run_comparison_agent
from src.agents.debate import run_debate_agent
from src.agents.citation_graph import build_citation_graph
from src.agents.report_generator import run_report_generator
from src.agents.critic import run_critic_agent

# Node names for progress tracking
PIPELINE_STEPS = [
    ("planner", "Research Planning"),
    ("search", "Paper Search"),
    ("filter", "Relevance Filtering"),
    ("pdf_reader", "PDF Extraction"),
    ("extractor", "Information Extraction"),
    ("comparison", "Comparative Analysis"),
    ("debate", "Multi-Agent Debate"),
    ("citation_graph", "Citation Graph"),
    ("report_generator", "Report Generation"),
    ("critic", "Quality Review"),
]


def _wrap_node(name: str, func: Callable, callback: Callable | None = None):
    """Wrap a node function with logging and optional UI callback."""
    def wrapper(state_dict: dict) -> dict:
        state = ResearchState(**state_dict)
        logger.info(f"▶ Entering node: [{name}]")
        try:
            updated_state = func(state)
        except Exception as e:
            logger.exception(f"❌ Node [{name}] failed: {e}")
            state.errors.append(f"{name}: {str(e)}")
            updated_state = state
        
        if callback:
            callback(name, updated_state)
        
        return updated_state.model_dump()
    return wrapper


def build_pipeline(callback: Callable | None = None):
    """Build and compile the LangGraph research pipeline."""
    if not LANGGRAPH_AVAILABLE:
        raise ImportError("langgraph not installed: pip install langgraph")

    graph = StateGraph(dict)

    # Add nodes
    graph.add_node("planner", _wrap_node("planner", run_planner_agent, callback))
    graph.add_node("search", _wrap_node("search", run_search_agent, callback))
    graph.add_node("filter", _wrap_node("filter", run_filter_agent, callback))
    graph.add_node("pdf_reader", _wrap_node("pdf_reader", run_pdf_reader_agent, callback))
    graph.add_node("extractor", _wrap_node("extractor", run_extractor_agent, callback))
    graph.add_node("comparison", _wrap_node("comparison", run_comparison_agent, callback))
    graph.add_node("debate", _wrap_node("debate", run_debate_agent, callback))
    graph.add_node("citation_graph", _wrap_node("citation_graph", build_citation_graph, callback))
    graph.add_node("report_generator", _wrap_node("report_generator", run_report_generator, callback))
    graph.add_node("critic", _wrap_node("critic", run_critic_agent, callback))

    # Define edges (linear pipeline)
    graph.add_edge(START, "planner")
    graph.add_edge("planner", "search")
    graph.add_edge("search", "filter")
    graph.add_edge("filter", "pdf_reader")
    graph.add_edge("pdf_reader", "extractor")
    graph.add_edge("extractor", "comparison")
    graph.add_edge("comparison", "debate")
    graph.add_edge("debate", "citation_graph")
    graph.add_edge("citation_graph", "report_generator")
    graph.add_edge("report_generator", "critic")
    graph.add_edge("critic", END)

    return graph.compile()


def run_research_pipeline(
    research_question: str,
    callback: Callable | None = None
) -> ResearchState:
    """
    Run the full research pipeline for a given question.
    
    Args:
        research_question: The research question to investigate
        callback: Optional function(node_name, state) called after each node
        
    Returns:
        Final ResearchState with report and all artifacts
    """
    logger.info(f"🚀 Starting research pipeline for: {research_question}")
    
    initial_state = ResearchState(
        research_question=research_question,
        status="initialized"
    )

    if LANGGRAPH_AVAILABLE:
        pipeline = build_pipeline(callback=callback)
        final_dict = pipeline.invoke(initial_state.model_dump())
        return ResearchState(**final_dict)
    else:
        # Fallback: run sequentially without LangGraph
        logger.warning("LangGraph not available. Running sequentially...")
        state = initial_state
        for func_name, func in [
            ("planner", run_planner_agent),
            ("search", run_search_agent),
            ("filter", run_filter_agent),
            ("pdf_reader", run_pdf_reader_agent),
            ("extractor", run_extractor_agent),
            ("comparison", run_comparison_agent),
            ("debate", run_debate_agent),
            ("citation_graph", build_citation_graph),
            ("report_generator", run_report_generator),
            ("critic", run_critic_agent),
        ]:
            try:
                state = func(state)
                if callback:
                    callback(func_name, state)
            except Exception as e:
                logger.error(f"Step {func_name} failed: {e}")
                state.errors.append(f"{func_name}: {str(e)}")
        return state
