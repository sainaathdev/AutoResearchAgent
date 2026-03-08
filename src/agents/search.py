"""
Search Agent
Searches ArXiv and Semantic Scholar for relevant papers.
Combines results and deduplicates.
"""

import time
import hashlib
import asyncio
from typing import Optional
import requests
from loguru import logger

try:
    import arxiv
    ARXIV_AVAILABLE = True
except ImportError:
    ARXIV_AVAILABLE = False

from src.config import (
    ResearchState, PaperMetadata,
    MAX_PAPERS_PER_SEARCH, SEMANTIC_SCHOLAR_API_KEY
)


def _make_paper_id(title: str, source: str) -> str:
    return hashlib.md5(f"{source}:{title.lower().strip()}".encode()).hexdigest()[:12]


# ─── ArXiv Search ─────────────────────────────────────────────────────────────

def search_arxiv(query: str, max_results: int = 15) -> list[PaperMetadata]:
    """Search ArXiv for papers matching the query."""
    if not ARXIV_AVAILABLE:
        logger.warning("arxiv package not installed")
        return []

    papers = []
    try:
        client = arxiv.Client(page_size=max_results, delay_seconds=2, num_retries=3)
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance,
            sort_order=arxiv.SortOrder.Descending,
        )

        for result in client.results(search):
            paper_id = _make_paper_id(result.title, "arxiv")
            pdf_url = None
            for link in result.links:
                if "pdf" in str(link.href):
                    pdf_url = str(link.href)
                    break
            if pdf_url is None:
                pdf_url = result.pdf_url

            papers.append(PaperMetadata(
                paper_id=paper_id,
                title=result.title,
                authors=[str(a) for a in result.authors],
                year=result.published.year if result.published else None,
                abstract=result.summary,
                url=str(result.entry_id),
                pdf_url=pdf_url,
                source="arxiv",
            ))

        logger.info(f"[Search/ArXiv] Found {len(papers)} papers for query: '{query[:60]}...'")
    except Exception as e:
        logger.error(f"[Search/ArXiv] Error: {e}")

    return papers


# ─── Semantic Scholar Search ───────────────────────────────────────────────────

def search_semantic_scholar(query: str, max_results: int = 15) -> list[PaperMetadata]:
    """Search Semantic Scholar API."""
    papers = []
    try:
        headers = {"Content-Type": "application/json"}
        if SEMANTIC_SCHOLAR_API_KEY:
            headers["x-api-key"] = SEMANTIC_SCHOLAR_API_KEY

        params = {
            "query": query,
            "limit": max_results,
            "fields": "title,authors,year,abstract,citationCount,externalIds,openAccessPdf,url"
        }

        resp = requests.get(
            "https://api.semanticscholar.org/graph/v1/paper/search",
            params=params,
            headers=headers,
            timeout=15
        )

        if resp.status_code == 200:
            data = resp.json()
            for item in data.get("data", []):
                paper_id = _make_paper_id(item.get("title", ""), "s2")
                pdf_url = None
                if item.get("openAccessPdf"):
                    pdf_url = item["openAccessPdf"].get("url")

                papers.append(PaperMetadata(
                    paper_id=paper_id,
                    title=item.get("title", ""),
                    authors=[a.get("name", "") for a in item.get("authors", [])],
                    year=item.get("year"),
                    abstract=item.get("abstract", ""),
                    url=item.get("url", ""),
                    pdf_url=pdf_url,
                    citation_count=item.get("citationCount", 0),
                    source="semantic_scholar",
                ))
            logger.info(f"[Search/S2] Found {len(papers)} papers for: '{query[:60]}'")
        elif resp.status_code == 429:
            logger.warning("[Search/S2] Rate limited. Sleeping 5s...")
            time.sleep(5)
        else:
            logger.warning(f"[Search/S2] HTTP {resp.status_code}")

    except Exception as e:
        logger.error(f"[Search/S2] Error: {e}")

    return papers


# ─── Deduplication ────────────────────────────────────────────────────────────

def _deduplicate(papers: list[PaperMetadata]) -> list[PaperMetadata]:
    """Remove duplicate papers by title similarity."""
    seen_titles: set[str] = set()
    unique = []
    for p in papers:
        norm = p.title.lower().strip()[:80]
        if norm not in seen_titles:
            seen_titles.add(norm)
            unique.append(p)
    return unique


# ─── Main Search Agent ────────────────────────────────────────────────────────

def run_search_agent(state: ResearchState) -> ResearchState:
    """Execute multi-source paper search."""
    logger.info("[Search Agent] Starting paper collection...")
    state.current_step = "searching"

    plan = state.research_plan
    if not plan:
        state.errors.append("No research plan found. Run planner first.")
        return state

    all_papers: list[PaperMetadata] = []

    # Build search queries from primary keywords + question
    queries = set()
    queries.add(state.research_question[:200])

    # Combine primary keywords into queries
    pkw = plan.primary_keywords
    if pkw:
        queries.add(" ".join(pkw[:3]))
        if len(pkw) > 3:
            queries.add(" ".join(pkw[3:6]))

    # Add sub-questions as queries (first 3)
    for sq in plan.sub_questions[:3]:
        queries.add(sq[:200])

    logger.info(f"[Search Agent] Running {len(queries)} queries...")

    for query in queries:
        # ArXiv
        arxiv_results = search_arxiv(query, max_results=10)
        all_papers.extend(arxiv_results)
        time.sleep(1)

        # Semantic Scholar
        s2_results = search_semantic_scholar(query, max_results=10)
        all_papers.extend(s2_results)
        time.sleep(1)

    # Deduplicate
    unique_papers = _deduplicate(all_papers)

    # Sort by citation count (prefer highly cited)
    unique_papers.sort(key=lambda p: p.citation_count, reverse=True)

    # Cap at max
    unique_papers = unique_papers[:MAX_PAPERS_PER_SEARCH]

    logger.success(f"[Search Agent] Collected {len(unique_papers)} unique papers total")
    state.raw_papers = unique_papers
    state.status = "searched"
    return state
