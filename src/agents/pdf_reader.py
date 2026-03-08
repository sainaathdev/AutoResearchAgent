"""
PDF Reader Agent
Downloads and extracts text from paper PDFs.
Caches downloaded PDFs to avoid re-fetching.
"""

import hashlib
import time
from pathlib import Path
import requests
from loguru import logger

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

from src.config import ResearchState, PDF_CACHE_DIR


def _pdf_cache_path(url: str) -> Path:
    """Generate a cache file path for a URL."""
    url_hash = hashlib.md5(url.encode()).hexdigest()[:16]
    return PDF_CACHE_DIR / f"{url_hash}.pdf"


def _txt_cache_path(url: str) -> Path:
    """Cache extracted text alongside the PDF."""
    url_hash = hashlib.md5(url.encode()).hexdigest()[:16]
    return PDF_CACHE_DIR / f"{url_hash}.txt"


def download_pdf(url: str) -> Path | None:
    """Download a PDF from URL, use cache if available."""
    cache_path = _pdf_cache_path(url)
    if cache_path.exists() and cache_path.stat().st_size > 1000:
        logger.debug(f"[PDF] Using cached: {cache_path.name}")
        return cache_path

    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (compatible; ResearchBot/1.0; "
                "+https://github.com/research-agent)"
            )
        }
        resp = requests.get(url, headers=headers, timeout=30, stream=True)
        if resp.status_code == 200 and "pdf" in resp.headers.get("content-type", "").lower():
            with open(cache_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.debug(f"[PDF] Downloaded: {cache_path.name} ({cache_path.stat().st_size} bytes)")
            return cache_path
        else:
            logger.warning(f"[PDF] Bad response {resp.status_code} for {url[:80]}")
    except Exception as e:
        logger.warning(f"[PDF] Download failed for {url[:80]}: {e}")
    return None


def extract_text_pymupdf(pdf_path: Path) -> str:
    """Extract text using PyMuPDF (fitz)."""
    text_parts = []
    try:
        doc = fitz.open(str(pdf_path))
        for page_num in range(min(len(doc), 20)):  # max 20 pages
            page = doc[page_num]
            text_parts.append(page.get_text())
        doc.close()
    except Exception as e:
        logger.warning(f"[PDF/PyMuPDF] Error: {e}")
    return "\n".join(text_parts)


def extract_text_pdfplumber(pdf_path: Path) -> str:
    """Extract text using pdfplumber."""
    text_parts = []
    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page in pdf.pages[:20]:
                txt = page.extract_text()
                if txt:
                    text_parts.append(txt)
    except Exception as e:
        logger.warning(f"[PDF/pdfplumber] Error: {e}")
    return "\n".join(text_parts)


def extract_pdf_text(pdf_path: Path) -> str:
    """Extract text from PDF, trying multiple methods."""
    txt_cache = _txt_cache_path(pdf_path.stem)
    # Re-use text cache if exists
    if txt_cache.exists():
        return txt_cache.read_text(encoding="utf-8", errors="ignore")

    text = ""
    if PYMUPDF_AVAILABLE:
        text = extract_text_pymupdf(pdf_path)
    if not text.strip() and PDFPLUMBER_AVAILABLE:
        text = extract_text_pdfplumber(pdf_path)

    if text.strip():
        txt_cache.write_text(text, encoding="utf-8", errors="ignore")

    return text


def run_pdf_reader_agent(state: ResearchState) -> ResearchState:
    """Download and extract text from all filtered papers."""
    logger.info(f"[PDF Reader] Processing {len(state.filtered_papers)} papers...")
    state.current_step = "pdf_reading"

    for i, paper in enumerate(state.filtered_papers):
        logger.info(f"[PDF Reader] {i+1}/{len(state.filtered_papers)}: {paper.title[:60]}...")

        if paper.full_text:
            logger.debug("[PDF Reader] Already has text, skipping")
            continue

        if not paper.pdf_url:
            logger.warning(f"[PDF Reader] No PDF URL for: {paper.title[:50]}")
            # Use abstract as fallback
            paper.full_text = paper.abstract or ""
            continue

        pdf_path = download_pdf(paper.pdf_url)
        if pdf_path:
            text = extract_pdf_text(pdf_path)
            if text.strip():
                paper.full_text = text[:15000]  # Cap at 15k chars to fit LLM context
                logger.success(f"[PDF Reader] Extracted {len(text)} chars")
            else:
                paper.full_text = paper.abstract or ""
                logger.warning("[PDF Reader] Empty extraction, using abstract")
        else:
            paper.full_text = paper.abstract or ""
            logger.warning("[PDF Reader] Download failed, using abstract")

        time.sleep(1)  # Be polite to servers

    state.status = "pdf_read"
    return state
