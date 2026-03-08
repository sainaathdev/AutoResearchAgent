"""
Multi-Agent Debate Module
Runs two debate agents: Optimistic Analyst vs Skeptical Reviewer.
Merges their perspectives into a balanced synthesis.
"""

from loguru import logger
from src.config import ResearchState
from src.llm import call_llm_safe

OPTIMIST_PROMPT = """You are an Optimistic Research Analyst.

Your job is to:
1. Highlight the most impressive achievements in the papers
2. Identify breakthrough ideas
3. Emphasize how results push the field forward
4. Identify the most promising future directions
5. Be enthusiastic but grounded in the data

Write 3–5 paragraphs of insightful, positive analysis."""

SKEPTIC_PROMPT = """You are a Skeptical Research Reviewer.

Your job is to:
1. Challenge bold claims made in the papers
2. Identify methodological weaknesses
3. Question whether improvements are statistically significant
4. Identify missing baselines or unfair comparisons
5. Highlight reproducibility concerns

Write 3–5 paragraphs of critical, grounded skepticism. Be constructive, not cynical."""

MERGER_PROMPT = """You are a Balanced Synthesis Agent.

You have received two perspectives on the same set of research papers:
- An optimistic analysis
- A skeptical review

Your job is to merge these into a balanced, nuanced perspective that:
1. Acknowledges genuine breakthroughs
2. Maintains honest assessment of limitations
3. Provides actionable insights
4. Reaches fair conclusions

Write a balanced synthesis of 4–6 paragraphs."""


def run_debate_agent(state: ResearchState) -> ResearchState:
    """Run the multi-agent debate and merge perspectives."""
    logger.info("[Debate Agent] Starting multi-agent debate...")
    state.current_step = "debate"

    if not state.filtered_papers:
        state.errors.append("No papers for debate.")
        return state

    # Build context for debate
    papers_context = []
    for p in state.filtered_papers:
        papers_context.append(
            f"- **{p.title}** ({p.year})\n"
            f"  Methodology: {p.methodology or 'N/A'}\n"
            f"  Results: {p.results or 'N/A'}\n"
            f"  Limitations: {p.limitations or 'N/A'}"
        )
    context = "\n".join(papers_context)

    papers_block = f"""Research Question: {state.research_question}

Papers being analyzed:
{context}"""

    try:
        # Optimistic Analyst
        logger.info("[Debate] Running Optimistic Analyst...")
        optimistic = call_llm_safe(papers_block, system=OPTIMIST_PROMPT, fallback="Analysis unavailable.")
        state.optimistic_view = optimistic

        # Skeptical Reviewer
        logger.info("[Debate] Running Skeptical Reviewer...")
        skeptical = call_llm_safe(papers_block, system=SKEPTIC_PROMPT, fallback="Review unavailable.")
        state.skeptical_view = skeptical

        # Merge perspectives
        logger.info("[Debate] Merging perspectives...")
        merge_prompt = f"""Optimistic Analysis:
{optimistic}

---

Skeptical Review:
{skeptical}

---

Now synthesize these two perspectives into a balanced view."""

        merged = call_llm_safe(merge_prompt, system=MERGER_PROMPT, fallback="Synthesis unavailable.")
        state.merged_perspective = merged

        logger.success("[Debate Agent] Debate complete")
    except Exception as e:
        logger.error(f"[Debate Agent] Error: {e}")
        state.errors.append(f"Debate error: {str(e)}")

    state.status = "debated"
    return state
