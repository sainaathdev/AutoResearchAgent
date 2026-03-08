"""
Citation Graph Builder
Builds a citation network from paper co-citations and identifies influential clusters.
Uses NetworkX for graph analysis.
"""

import re
import hashlib
from collections import defaultdict
from loguru import logger

try:
    import networkx as nx
    NX_AVAILABLE = True
except ImportError:
    NX_AVAILABLE = False

from src.config import ResearchState


def _normalize_title(title: str) -> str:
    """Normalize paper title for matching."""
    return re.sub(r"[^a-z0-9 ]", "", title.lower().strip())


def _find_citations_in_text(text: str, known_papers: list) -> list[tuple[str, str]]:
    """Find which known papers are cited in a given paper's text."""
    edges = []
    if not text:
        return edges

    text_lower = text.lower()
    for candidate in known_papers:
        norm = _normalize_title(candidate.title)
        # Check first 60 chars of title
        key = norm[:60]
        if key and len(key) > 20 and key in text_lower:
            edges.append(("self", candidate.paper_id))

    return edges


def build_citation_graph(state: ResearchState) -> ResearchState:
    """Build citation graph from paper full texts."""
    logger.info("[Citation Graph] Building citation network...")

    papers = state.filtered_papers
    if not papers:
        return state

    edges = []

    for paper in papers:
        if not paper.full_text:
            continue

        # Check if this paper's text cites other analyzed papers
        other_papers = [p for p in papers if p.paper_id != paper.paper_id]
        for other in other_papers:
            norm_title = _normalize_title(other.title)[:60]
            if norm_title and len(norm_title) > 15:
                if norm_title in paper.full_text.lower():
                    edges.append({
                        "source": paper.paper_id,
                        "source_title": paper.title,
                        "target": other.paper_id,
                        "target_title": other.title,
                    })

    state.citation_edges = edges
    logger.info(f"[Citation Graph] Found {len(edges)} citation relationships")

    # Compute centrality if networkx available
    if NX_AVAILABLE and edges:
        G = nx.DiGraph()
        for p in papers:
            G.add_node(p.paper_id, title=p.title, year=p.year)
        for e in edges:
            G.add_edge(e["source"], e["target"])

        try:
            centrality = nx.pagerank(G)
            # Add centrality rankings to state metadata
            sorted_central = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
            logger.info("[Citation Graph] Most influential papers by PageRank:")
            for pid, score in sorted_central[:5]:
                node = G.nodes.get(pid, {})
                logger.info(f"  {node.get('title', pid)[:60]}: {score:.4f}")
        except Exception as e:
            logger.warning(f"[Citation Graph] PageRank failed: {e}")

    return state
