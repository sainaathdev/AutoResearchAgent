"""
Report Generator Agent
Produces the final structured Markdown research report.
Falls back to a fully data-driven template report when LLM fails.
"""

import json
from datetime import datetime
from loguru import logger
from src.config import ResearchState, OUTPUT_DIR
from src.llm import call_llm_safe


SYSTEM_PROMPT = """You are an Expert Research Report Writer.

Given paper data and analysis, write specific sections for a research report.
Write in clear academic prose. Base all claims on the provided paper data.
Do NOT invent results. Mark uncertain information with (inferred)."""


def _build_papers_table(papers) -> str:
    rows = [
        "| # | Title | Authors | Year | Source | Relevance |",
        "|---|-------|---------|------|--------|-----------|",
    ]
    for i, p in enumerate(papers, 1):
        authors_str = ", ".join(p.authors[:2]) + (" et al." if len(p.authors) > 2 else "")
        title_short = p.title[:65] + ("..." if len(p.title) > 65 else "")
        url = p.url or "#"
        rows.append(
            f"| {i} | [{title_short}]({url}) | {authors_str} | "
            f"{p.year or 'N/A'} | {p.source} | {p.relevance_score:.2f} |"
        )
    return "\n".join(rows)


def _build_extraction_table(papers) -> str:
    rows = [
        "| Title | Methodology | Dataset | Metrics | Key Limitation |",
        "|-------|-------------|---------|---------|----------------|",
    ]
    for p in papers:
        title_short = (p.title[:38] + "...") if len(p.title) > 38 else p.title
        methodology = ((p.methodology or "N/A")[:60]).replace("|", "/")
        dataset     = ((p.dataset or "N/A")[:40]).replace("|", "/")
        metrics     = ((p.metrics or "N/A")[:40]).replace("|", "/")
        limitations = ((p.limitations or "N/A")[:60]).replace("|", "/")
        rows.append(f"| {title_short} | {methodology} | {dataset} | {metrics} | {limitations} |")
    return "\n".join(rows)


def _build_fallback_sections(papers, analysis, state) -> str:
    """Generate report narrative purely from extracted data — no LLM needed."""
    lines = []

    # Executive summary from paper abstracts
    lines.append("## 📋 Executive Summary\n")
    lines.append(
        f"This report analyzes **{len(papers)} research papers** related to: "
        f"*{state.research_question}*. Papers were retrieved from ArXiv and Semantic Scholar, "
        f"filtered by relevance, and key information was extracted automatically.\n"
    )
    for p in papers[:3]:
        contrib = p.key_contributions or p.abstract or ""
        if contrib:
            lines.append(f"- **{p.title}** ({p.year}): {contrib[:200]}")
    lines.append("")

    # Trend Analysis from comparison agent
    if analysis and analysis.innovation_trends:
        lines.append("## 📈 Trend Analysis\n")
        for t in analysis.innovation_trends:
            lines.append(f"- {t}")
        lines.append("")

    # Research Gaps from limitations
    lines.append("## 🕳️ Research Gaps\n")
    all_limitations = [p.limitations for p in papers if p.limitations]
    if all_limitations:
        for lim in all_limitations[:5]:
            lines.append(f"- {lim[:150]}")
    elif analysis and analysis.recurring_limitations:
        for lim in analysis.recurring_limitations:
            lines.append(f"- {lim}")
    else:
        lines.append("- Further study needed to identify specific gaps.")
    lines.append("")

    # Future Directions
    lines.append("## 🚀 Future Directions\n")
    lines.append(
        "Based on the identified limitations and current trends, promising future directions include:"
    )
    lines.append("- Improving computational efficiency of current approaches")
    lines.append("- Better evaluation benchmarks and standardized metrics")
    lines.append("- Cross-domain generalization of proposed methods")
    lines.append("- Addressing reproducibility and open-source tooling")
    lines.append("")

    return "\n".join(lines)


def run_report_generator(state: ResearchState) -> ResearchState:
    """Generate the final research report."""
    logger.info("[Report Generator] Generating final report...")
    state.current_step = "generating_report"

    papers = state.filtered_papers
    plan = state.research_plan
    analysis = state.comparative_analysis

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    papers_table = _build_papers_table(papers)
    extraction_table = _build_extraction_table(papers)

    # ── Try LLM for narrative sections ───────────────────────────────────────
    papers_data = []
    for p in papers:
        papers_data.append({
            "title": p.title, "year": p.year,
            "methodology": p.methodology, "results": p.results,
            "limitations": p.limitations, "key_contributions": p.key_contributions,
        })

    prompt = (
        f"Research Question: {state.research_question}\n\n"
        f"Papers Analyzed ({len(papers)} total):\n"
        f"{json.dumps(papers_data[:6], indent=2)}\n\n"  # cap at 6 papers for prompt size
        f"Trends: {json.dumps((analysis.innovation_trends if analysis else [])[:5])}\n"
        f"Limitations: {json.dumps((analysis.recurring_limitations if analysis else [])[:5])}\n\n"
        f"Write these sections ONLY (no headers, just flowing prose):\n"
        f"1. Executive Summary (3 paragraphs)\n"
        f"2. Trend Analysis (2 paragraphs)\n"
        f"3. Research Gaps (bullet points)\n"
        f"4. Future Directions (bullet points)"
    )

    narrative = call_llm_safe(
        prompt,
        system=SYSTEM_PROMPT,
        fallback="",
        temperature=0.2
    )

    # If LLM failed, build a data-driven fallback narrative
    if not narrative.strip() or len(narrative) < 100:
        logger.warning("[Report Generator] LLM failed/empty — using data-driven fallback.")
        narrative = _build_fallback_sections(papers, analysis, state)

    # ── Performance ranking ───────────────────────────────────────────────────
    performance_ranking = ""
    if analysis and analysis.performance_ranking:
        for item in analysis.performance_ranking[:5]:
            performance_ranking += f"- **#{item.get('rank','?')} {item.get('paper','?')}**: {item.get('reason','')}\n"
    else:
        # Fallback: rank by citation count
        sorted_papers = sorted(papers, key=lambda p: p.citation_count, reverse=True)
        for i, p in enumerate(sorted_papers[:5], 1):
            performance_ranking += f"- **#{i} {p.title[:60]}**: {p.citation_count} citations\n"

    # ── Debate sections ───────────────────────────────────────────────────────
    optimistic_block = (
        f"\n### 🔬 Optimistic Analysis\n{state.optimistic_view}\n"
        if state.optimistic_view else ""
    )
    skeptical_block = (
        f"\n### 🔍 Skeptical Review\n{state.skeptical_view}\n"
        if state.skeptical_view else ""
    )
    merged_block = (
        f"\n### ⚖️ Balanced Synthesis\n{state.merged_perspective}\n"
        if state.merged_perspective else ""
    )

    # ── Innovation trends list ────────────────────────────────────────────────
    trends_list = (
        "".join(f"- {t}\n" for t in (analysis.innovation_trends if analysis else []))
        or "- Analysis data insufficient for trend identification.\n"
    )
    limitations_list = (
        "".join(f"- {l}\n" for l in (analysis.recurring_limitations if analysis else []))
        or "- See individual paper limitations in the table above.\n"
    )

    # ── Metrics comparison ────────────────────────────────────────────────────
    metrics_comp = (analysis.metrics_comparison if analysis else "") or "_Not available._"
    methodology_comp = (analysis.methodology_comparison if analysis else "") or "_Not available._"

    # ── Assemble full report ──────────────────────────────────────────────────
    avg_rel = sum(p.relevance_score for p in papers) / max(len(papers), 1)
    pdf_count = sum(1 for p in papers if p.full_text and len(p.full_text) > 200)

    report = f"""# 📚 Autonomous Research Report

> **Research Question:** {state.research_question}
> **Generated:** {now}
> **Papers Analyzed:** {len(papers)}
> **Confidence Score:** {state.confidence_score:.1%}

---

{narrative}

---

## 📄 Selected Papers

{papers_table}

---

## 🔬 Detailed Paper Information

{extraction_table}

---

## ⚙️ Methodology Comparison

{methodology_comp}

---

## 📊 Performance Comparison

### Ranking (by citation count / LLM analysis)
{performance_ranking}

### Metrics Comparison
{metrics_comp}

---

## 🧠 Multi-Agent Debate
{optimistic_block}
{skeptical_block}
{merged_block}

---

## 📈 Key Trends

{trends_list}

---

## 🕳️ Recurring Limitations

{limitations_list}

---

## 📊 Confidence Score

**Overall Confidence: {state.confidence_score:.1%}**

| Factor | Assessment |
|--------|------------|
| Papers Found | {len(state.raw_papers)} total |
| Papers Included | {len(papers)} |
| PDF Full-Text Available | {pdf_count} |
| Avg Relevance Score | {avg_rel:.2f} |

---

*Report generated by Autonomous Research Agent · {now}*
"""

    state.final_report = report
    state.status = "report_generated"

    # Save report to disk
    safe_name = "".join(
        c if c.isalnum() or c in " _-" else "_"
        for c in state.research_question[:50]
    ).strip()
    report_path = OUTPUT_DIR / f"report_{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    report_path.write_text(report, encoding="utf-8")
    logger.success(f"[Report Generator] Saved to: {report_path}")

    return state
