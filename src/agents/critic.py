"""
Critic Agent
Quality control agent that reviews the generated report for:
- Hallucinated claims
- Fabricated citations
- Logical flaws
- Unsupported assertions
"""

import json
from loguru import logger
from src.config import ResearchState, CriticReport
from src.llm import call_llm_json_safe

SYSTEM_PROMPT = """You are a Research Quality Control Agent (Critic).

Your task is to review a research report and assess its quality.
Check:
1. Are any claims unsupported by the analyzed papers?
2. Are any papers misrepresented?
3. Are there logically flawed comparisons?
4. Are the research gaps justified by the evidence?
5. Is the confidence score appropriate given the data?

Be specific. Cite evidence. Be constructive.

Return ONLY valid JSON in this exact format:
{
  "hallucination_detected": false,
  "unsupported_claims": ["Claim 1...", "Claim 2..."],
  "logical_flaws": ["Flaw 1...", "Flaw 2..."],
  "overall_quality_score": 0.85,
  "suggestions_for_improvement": ["Suggestion 1...", "Suggestion 2..."]
}
"""


def run_critic_agent(state: ResearchState) -> ResearchState:
    """Review the research report for quality and hallucinations."""
    logger.info("[Critic Agent] Reviewing report quality...")
    state.current_step = "critic_review"

    if not state.final_report:
        state.errors.append("No report to review.")
        return state

    # Build paper groundtruth summary for critic
    paper_facts = []
    for p in state.filtered_papers:
        paper_facts.append({
            "title": p.title,
            "year": p.year,
            "stated_methodology": p.methodology,
            "stated_results": p.results,
            "stated_limitations": p.limitations,
        })

    prompt = f"""Research Question: {state.research_question}

Ground Truth - Extracted Paper Facts:
{json.dumps(paper_facts, indent=2)}

Report to Review:
{state.final_report[:5000]}

Review this report thoroughly for accuracy, hallucinations, and logical soundness."""

    try:
        result = call_llm_json_safe(prompt, system=SYSTEM_PROMPT, fallback={})

        critic = CriticReport(
            hallucination_detected=bool(result.get("hallucination_detected", False)),
            unsupported_claims=result.get("unsupported_claims", []),
            logical_flaws=result.get("logical_flaws", []),
            overall_quality_score=float(result.get("overall_quality_score", 0.7)),
            suggestions_for_improvement=result.get("suggestions_for_improvement", []),
        )
        state.critic_report = critic
        state.confidence_score = critic.overall_quality_score

        logger.success(
            f"[Critic Agent] Quality score: {critic.overall_quality_score:.2f} | "
            f"Hallucination: {critic.hallucination_detected}"
        )
    except Exception as e:
        logger.error(f"[Critic Agent] Error: {e}")
        state.errors.append(f"Critic error: {str(e)}")
        state.critic_report = CriticReport(
            overall_quality_score=0.5,
            suggestions_for_improvement=["Critic failed to run — manual review recommended"]
        )
        state.confidence_score = 0.5

    state.status = "reviewed"
    return state
