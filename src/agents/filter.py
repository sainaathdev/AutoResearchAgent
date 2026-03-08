"""
Paper Filtering Agent
Scores each paper's relevance to the research question.
Uses LLM scoring with a robust keyword-based fallback.
Always guarantees a minimum number of papers pass through.
"""

from loguru import logger
from src.config import ResearchState, PaperMetadata, RELEVANCE_THRESHOLD, MAX_PAPERS_TO_PROCESS
from src.llm import call_llm_json_safe

SYSTEM_PROMPT = """You are a Paper Relevance Evaluator for academic research.

Given a research question and a paper title + abstract, return ONLY this JSON:
{
  "relevance_score": 0.85,
  "decision": "include",
  "reasoning": "Brief reason"
}

Rules:
- relevance_score: 0.0 to 1.0
- decision: exactly "include" or "discard"
- Be generous — if the paper is even remotely related, include it
- Do NOT add any text outside the JSON
"""

# Minimum papers to always pass through (even if scores are low)
MIN_PAPERS_GUARANTEED = 3


def _keyword_score(paper: PaperMetadata, research_question: str) -> float:
    """Fast keyword-overlap relevance score as fallback."""
    # Extract meaningful words (length > 3) from the question
    stop_words = {"what", "are", "the", "for", "and", "with", "that", "this",
                  "from", "have", "has", "been", "will", "their", "these"}
    question_words = [
        w.lower().strip("?.,") for w in research_question.split()
        if len(w) > 3 and w.lower() not in stop_words
    ]
    if not question_words:
        return 0.5

    paper_text = f"{paper.title} {paper.abstract or ''}".lower()
    hits = sum(1 for w in question_words if w in paper_text)
    score = min(hits / len(question_words), 1.0)

    # Boost for highly-cited papers (they're usually relevant)
    if paper.citation_count > 100:
        score = min(score + 0.15, 1.0)
    elif paper.citation_count > 20:
        score = min(score + 0.08, 1.0)

    return round(score, 3)


def filter_single_paper(paper: PaperMetadata, research_question: str) -> PaperMetadata:
    """Score a single paper's relevance. Never raises."""
    abstract_snippet = (paper.abstract or "")[:600]

    prompt = (
        f"Research Question: {research_question}\n\n"
        f"Paper Title: {paper.title}\n"
        f"Abstract: {abstract_snippet}\n"
        f"Year: {paper.year}  Citations: {paper.citation_count}\n\n"
        f"Rate relevance as JSON."
    )

    result = call_llm_json_safe(
        prompt,
        system=SYSTEM_PROMPT,
        fallback={}     # empty → triggers keyword fallback below
    )

    # Parse LLM result
    score = result.get("relevance_score")
    decision = result.get("decision", "")

    if score is not None:
        try:
            paper.relevance_score = float(score)
            paper.relevance_decision = "include" if decision == "include" else "discard"
            paper.relevance_reasoning = result.get("reasoning", "LLM scored")
            return paper
        except (ValueError, TypeError):
            pass

    # Fallback: keyword scoring
    kw_score = _keyword_score(paper, research_question)
    paper.relevance_score = kw_score
    paper.relevance_decision = "include" if kw_score >= RELEVANCE_THRESHOLD else "discard"
    paper.relevance_reasoning = f"Keyword fallback score: {kw_score:.2f}"
    logger.debug(f"[Filter] Keyword fallback for '{paper.title[:50]}': {kw_score:.2f}")
    return paper


def run_filter_agent(state: ResearchState) -> ResearchState:
    """Filter papers by relevance — guarantees MIN_PAPERS_GUARANTEED pass through."""
    logger.info(f"[Filter Agent] Evaluating {len(state.raw_papers)} papers...")
    state.current_step = "filtering"

    if not state.raw_papers:
        state.errors.append("No papers to filter.")
        return state

    scored_papers = []
    for i, paper in enumerate(state.raw_papers):
        logger.info(f"[Filter] {i+1}/{len(state.raw_papers)}: {paper.title[:60]}...")
        scored = filter_single_paper(paper, state.research_question)
        scored_papers.append(scored)

    # Sort all by relevance score descending
    scored_papers.sort(key=lambda p: p.relevance_score, reverse=True)

    # Primary: papers above threshold
    included = [
        p for p in scored_papers
        if p.relevance_decision == "include" and p.relevance_score >= RELEVANCE_THRESHOLD
    ]

    # Safety net: if fewer than MIN_PAPERS_GUARANTEED pass, force-include the top scorers
    if len(included) < MIN_PAPERS_GUARANTEED:
        logger.warning(
            f"[Filter] Only {len(included)} papers above threshold "
            f"({RELEVANCE_THRESHOLD}). Force-including top {MIN_PAPERS_GUARANTEED}."
        )
        included = scored_papers[:MIN_PAPERS_GUARANTEED]
        for p in included:
            p.relevance_decision = "include"

    # Cap at max
    included = included[:MAX_PAPERS_TO_PROCESS]

    avg_score = sum(p.relevance_score for p in included) / max(len(included), 1)
    logger.success(
        f"[Filter Agent] {len(included)} papers selected "
        f"(avg relevance: {avg_score:.2f})"
    )
    state.filtered_papers = included
    state.status = "filtered"
    return state
