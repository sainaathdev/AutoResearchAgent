"""
Comparison Agent
Performs structured comparative analysis across extracted papers.
Identifies trends, differences, and recurring weaknesses.
"""

from loguru import logger
from src.config import ResearchState, ComparativeAnalysis
from src.llm import call_llm_json_safe

SYSTEM_PROMPT = """You are a Comparative Research Analyst.

Given structured data from multiple research papers, produce a comparative analysis.
Return ONLY valid JSON in this exact format:
{
  "methodology_comparison": "Detailed narrative comparing approaches...",
  "dataset_comparison": "Comparison of datasets used...",
  "metrics_comparison": "Comparison of evaluation metrics...",
  "performance_ranking": [
    {"rank": 1, "paper": "Title", "reason": "Best because..."},
    {"rank": 2, "paper": "Title", "reason": "..."}
  ],
  "innovation_trends": [
    "Trend 1: ...",
    "Trend 2: ..."
  ],
  "recurring_limitations": [
    "Limitation 1: ...",
    "Limitation 2: ..."
  ]
}
"""


def run_comparison_agent(state: ResearchState) -> ResearchState:
    """Build comparative analysis across all extracted papers."""
    logger.info(f"[Comparison Agent] Comparing {len(state.filtered_papers)} papers...")
    state.current_step = "comparing"

    if len(state.filtered_papers) < 2:
        logger.warning("[Comparison] Not enough papers to compare.")
        state.comparative_analysis = ComparativeAnalysis(
            methodology_comparison="Insufficient papers for comparison.",
            innovation_trends=["Only one paper found"],
            recurring_limitations=[]
        )
        return state

    # Build a compact summary of each paper for the LLM
    papers_summary = []
    for p in state.filtered_papers:
        summary = {
            "title": p.title,
            "year": p.year,
            "methodology": p.methodology or "N/A",
            "dataset": p.dataset or "N/A",
            "metrics": p.metrics or "N/A",
            "results": p.results or "N/A",
            "limitations": p.limitations or "N/A",
            "key_contributions": p.key_contributions or "N/A",
        }
        papers_summary.append(summary)

    import json
    prompt = f"""Research Question: {state.research_question}

Papers Data:
{json.dumps(papers_summary, indent=2)}

Perform a comprehensive comparative analysis of these {len(papers_summary)} papers."""

    try:
        result = call_llm_json_safe(prompt, system=SYSTEM_PROMPT, fallback={})

        analysis = ComparativeAnalysis(
            methodology_comparison=result.get("methodology_comparison", ""),
            dataset_comparison=result.get("dataset_comparison", ""),
            metrics_comparison=result.get("metrics_comparison", ""),
            performance_ranking=result.get("performance_ranking", []),
            innovation_trends=result.get("innovation_trends", []),
            recurring_limitations=result.get("recurring_limitations", []),
        )
        state.comparative_analysis = analysis
        logger.success("[Comparison Agent] Analysis complete")
    except Exception as e:
        logger.error(f"[Comparison Agent] Error: {e}")
        state.errors.append(f"Comparison error: {str(e)}")
        state.comparative_analysis = ComparativeAnalysis()

    state.status = "compared"
    return state
