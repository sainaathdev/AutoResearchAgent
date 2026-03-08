"""
Information Extractor Agent
Uses LLM to extract structured information from each paper's full text.
"""

from loguru import logger
from src.config import ResearchState, PaperMetadata
from src.llm import call_llm_json_safe

SYSTEM_PROMPT = """You are a Research Paper Information Extractor.

Extract the following structured information from the given paper text.
Only extract information explicitly present in the text.
If a field is missing or unclear, use null.
Do NOT hallucinate or invent information.

Return ONLY valid JSON in this exact format:
{
  "problem_statement": "...",
  "methodology": "...",
  "dataset": "...",
  "metrics": "...",
  "results": "...",
  "limitations": "...",
  "key_contributions": "..."
}
"""


def extract_paper_info(paper: PaperMetadata) -> PaperMetadata:
    """Extract structured information from a paper."""
    if not paper.full_text and not paper.abstract:
        logger.warning(f"[Extractor] No text for: {paper.title[:50]}")
        return paper

    # Use full text if available, else abstract
    text = paper.full_text or paper.abstract or ""
    # Truncate to fit LLM context
    text_snippet = text[:6000]

    prompt = f"""Paper Title: {paper.title}
Authors: {', '.join(paper.authors[:5])}
Year: {paper.year}

Paper Text:
{text_snippet}

Extract the structured information from this paper."""

    try:
        result = call_llm_json_safe(prompt, system=SYSTEM_PROMPT, fallback={})

        paper.problem_statement = result.get("problem_statement")
        paper.methodology = result.get("methodology")
        paper.dataset = result.get("dataset")
        paper.metrics = result.get("metrics")
        paper.results = result.get("results")
        paper.limitations = result.get("limitations")
        paper.key_contributions = result.get("key_contributions")

        logger.success(f"[Extractor] Extracted info for: {paper.title[:50]}")
    except Exception as e:
        logger.error(f"[Extractor] Failed for '{paper.title[:50]}': {e}")

    return paper


def run_extractor_agent(state: ResearchState) -> ResearchState:
    """Extract structured info from all filtered papers."""
    logger.info(f"[Extractor Agent] Extracting from {len(state.filtered_papers)} papers...")
    state.current_step = "extracting"

    for i, paper in enumerate(state.filtered_papers):
        logger.info(f"[Extractor] {i+1}/{len(state.filtered_papers)}: {paper.title[:60]}...")
        state.filtered_papers[i] = extract_paper_info(paper)

    state.status = "extracted"
    return state
