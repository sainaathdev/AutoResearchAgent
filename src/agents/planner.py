"""
Research Planner Agent
Breaks the research question into sub-questions, identifies keywords,
and defines search strategy.
"""

from loguru import logger
from src.config import ResearchPlan, ResearchState
from src.llm import call_llm_json_safe

SYSTEM_PROMPT = """You are a Research Planning Agent for academic research.
Given a research question, your job is to:
1. Break it into 3–7 focused sub-questions
2. Identify primary and secondary keywords (with synonyms and technical variants)
3. Define a search strategy

Return ONLY valid JSON in this exact format:
{
  "sub_questions": ["...", "..."],
  "primary_keywords": ["...", "..."],
  "secondary_keywords": ["...", "..."],
  "search_strategy": {
    "time_range": "2020-2025",
    "prefer_recent": true,
    "min_citation_count": 5,
    "target_conferences": ["NeurIPS", "CVPR", "ICLR", "ICML", "ECCV"],
    "foundational_papers_needed": true,
    "max_papers": 20
  }
}"""


def run_planner_agent(state: ResearchState) -> ResearchState:
    """Execute the Research Planner Agent."""
    logger.info(f"[Planner] Planning research for: {state.research_question}")
    state.current_step = "planning"

    prompt = f"""Research Question: {state.research_question}

Analyze this question and produce a comprehensive research plan."""

    try:
        result = call_llm_json_safe(prompt, system=SYSTEM_PROMPT, fallback={})

        plan = ResearchPlan(
            original_question=state.research_question,
            sub_questions=result.get("sub_questions", []),
            primary_keywords=result.get("primary_keywords", []),
            secondary_keywords=result.get("secondary_keywords", []),
            search_strategy=result.get("search_strategy", {})
        )
        state.research_plan = plan
        logger.success(f"[Planner] Generated {len(plan.sub_questions)} sub-questions, "
                       f"{len(plan.primary_keywords)} primary keywords")
    except Exception as e:
        logger.error(f"[Planner] Error: {e}")
        state.errors.append(f"Planner error: {str(e)}")
        # Fallback: extract keywords from question directly
        words = state.research_question.split()
        state.research_plan = ResearchPlan(
            original_question=state.research_question,
            sub_questions=[state.research_question],
            primary_keywords=[w for w in words if len(w) > 4][:5],
            secondary_keywords=[],
            search_strategy={"time_range": "2020-2025", "max_papers": 20}
        )

    state.status = "planned"
    return state
