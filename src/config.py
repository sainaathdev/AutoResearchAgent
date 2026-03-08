"""
Core configuration and shared types for the Autonomous Research Agent.
"""

import os
from pathlib import Path
from typing import Any, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# ─── Paths ───────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DB_PATH = Path(os.getenv("CHROMA_DB_PATH", str(DATA_DIR / "chroma_db")))
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", str(DATA_DIR / "reports")))
PDF_CACHE_DIR = Path(os.getenv("PDF_CACHE_DIR", str(DATA_DIR / "pdf_cache")))

for _p in [DATA_DIR, CHROMA_DB_PATH, OUTPUT_DIR, PDF_CACHE_DIR]:
    _p.mkdir(parents=True, exist_ok=True)

# ─── LLM Config ──────────────────────────────────────────────────────────────
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0.1"))

# ─── Search Config ────────────────────────────────────────────────────────────
SEMANTIC_SCHOLAR_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")
MAX_PAPERS_PER_SEARCH = int(os.getenv("MAX_PAPERS_PER_SEARCH", "20"))
MAX_PAPERS_TO_PROCESS = int(os.getenv("MAX_PAPERS_TO_PROCESS", "10"))
RELEVANCE_THRESHOLD = float(os.getenv("RELEVANCE_THRESHOLD", "0.4"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")


# ─── Pydantic Models (Shared State) ──────────────────────────────────────────

class PaperMetadata(BaseModel):
    """Structured representation of a research paper."""
    paper_id: str
    title: str
    authors: list[str] = []
    year: Optional[int] = None
    abstract: Optional[str] = None
    url: Optional[str] = None
    pdf_url: Optional[str] = None
    citation_count: int = 0
    source: str = "arxiv"  # arxiv | semantic_scholar

    # Extracted fields (populated after PDF reading)
    problem_statement: Optional[str] = None
    methodology: Optional[str] = None
    dataset: Optional[str] = None
    metrics: Optional[str] = None
    results: Optional[str] = None
    limitations: Optional[str] = None
    key_contributions: Optional[str] = None

    # Relevance filtering
    relevance_score: float = 0.0
    relevance_decision: str = "pending"  # pending | include | discard
    relevance_reasoning: Optional[str] = None

    # Full text (cached)
    full_text: Optional[str] = None


class ResearchPlan(BaseModel):
    """Output of the Research Planner Agent."""
    original_question: str
    sub_questions: list[str] = []
    primary_keywords: list[str] = []
    secondary_keywords: list[str] = []
    search_strategy: dict[str, Any] = {}


class ComparativeAnalysis(BaseModel):
    """Output of the Comparison Agent."""
    methodology_comparison: str = ""
    dataset_comparison: str = ""
    metrics_comparison: str = ""
    performance_ranking: list[dict] = []
    innovation_trends: list[str] = []
    recurring_limitations: list[str] = []


class CriticReport(BaseModel):
    """Output of the Critic Agent."""
    hallucination_detected: bool = False
    unsupported_claims: list[str] = []
    logical_flaws: list[str] = []
    overall_quality_score: float = 0.0
    suggestions_for_improvement: list[str] = []


class ResearchState(BaseModel):
    """Master state object passed through the LangGraph pipeline."""
    # Input
    research_question: str = ""

    # Planning
    research_plan: Optional[ResearchPlan] = None

    # Search results
    raw_papers: list[PaperMetadata] = []
    filtered_papers: list[PaperMetadata] = []

    # Analysis
    comparative_analysis: Optional[ComparativeAnalysis] = None

    # Debate
    optimistic_view: Optional[str] = None
    skeptical_view: Optional[str] = None
    merged_perspective: Optional[str] = None

    # Final outputs
    final_report: Optional[str] = None
    critic_report: Optional[CriticReport] = None

    # Citation graph
    citation_edges: list[dict] = []

    # Meta
    status: str = "initialized"
    errors: list[str] = []
    current_step: str = ""
    confidence_score: float = 0.0
