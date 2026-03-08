# Autonomous Research Agent

> A production-grade, multi-agent system for autonomous academic research using LangGraph + Ollama + ArXiv/Semantic Scholar.

---

## 🏗️ Architecture

```
User Query
    ↓
Research Planner Agent    ← Breaks into sub-questions + keywords
    ↓
Search Agent              ← ArXiv + Semantic Scholar
    ↓
Paper Filtering Agent     ← LLM relevance scoring
    ↓
PDF Reader Agent          ← Download + extract text
    ↓
Information Extractor     ← Methodology, datasets, metrics, limitations
    ↓
Comparison Agent          ← Cross-paper analysis
    ↓
Multi-Agent Debate        ← Optimist vs Skeptic → Merged synthesis
    ↓
Citation Graph Builder    ← PageRank influence scores
    ↓
Report Generator          ← Full structured Markdown report
    ↓
Critic Agent              ← Hallucination detection + quality score
```

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.11+
- [Ollama](https://ollama.ai) installed and running
- At least one LLaMA model pulled

### 2. Setup

```powershell
# Create & activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Copy environment config
cp .env.example .env

# Pull an Ollama model (if not done)
ollama pull llama3.2

# Run setup checker
python setup_check.py
```

### 3. Launch Streamlit UI

```powershell
streamlit run app.py
```

### 4. Use CLI

```powershell
# Basic usage
python main.py -q "What are the latest advancements in diffusion-based video generation?"

# With preview
python main.py -q "Survey of RLHF methods" --preview

# JSON output
python main.py -q "3D neural rendering" --json-output
```

---

## 📁 Project Structure

```
autoReAgent/
├── app.py                    # Streamlit UI
├── main.py                   # CLI entry point
├── setup_check.py            # Environment verification
├── requirements.txt
├── .env.example
├── src/
│   ├── config.py             # Config + shared Pydantic models
│   ├── llm.py                # Ollama LLM wrapper
│   ├── pipeline.py           # LangGraph orchestrator
│   └── agents/
│       ├── planner.py        # Research Planner Agent
│       ├── search.py         # Search Agent (ArXiv + S2)
│       ├── filter.py         # Paper Filtering Agent
│       ├── pdf_reader.py     # PDF Download + Extraction
│       ├── extractor.py      # Information Extractor Agent
│       ├── comparison.py     # Comparative Analysis Agent
│       ├── debate.py         # Multi-Agent Debate (Optimist + Skeptic)
│       ├── citation_graph.py # Citation Graph + PageRank
│       ├── report_generator.py # Final Report Generator
│       └── critic.py         # Quality Control / Critic Agent
├── data/
│   ├── reports/              # Generated Markdown reports
│   ├── pdf_cache/            # Cached PDFs + text
│   └── chroma_db/            # Vector store
└── venv/
```

---

## 🧠 Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM | Ollama (Llama 3.2, Mistral, Mixtral) |
| Agent Framework | LangGraph |
| Paper Search | ArXiv API + Semantic Scholar API |
| PDF Processing | PyMuPDF + pdfplumber |
| Embeddings | SentenceTransformers (all-MiniLM-L6-v2) |
| Vector DB | ChromaDB |
| Graph Analysis | NetworkX + PageRank |
| UI | Streamlit |
| Visualization | Plotly |

---

## 🎛️ Configuration (`.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.2` | Default model |
| `MAX_PAPERS_PER_SEARCH` | `20` | Papers to fetch |
| `MAX_PAPERS_TO_PROCESS` | `10` | Papers to fully analyze |
| `RELEVANCE_THRESHOLD` | `0.6` | Min relevance score |
| `SEMANTIC_SCHOLAR_API_KEY` | _(empty)_ | Optional S2 API key |

---

## 📊 Output Report Format

Each run generates a Markdown report including:

- **Executive Summary**
- **Selected Papers Table** (with relevance scores)
- **Detailed Paper Information** (methodology, datasets, metrics, limitations)
- **Methodology Comparison**
- **Performance Comparison & Ranking**
- **Multi-Agent Debate** (Optimist + Skeptic + Synthesis)
- **Trend Analysis**
- **Research Gaps**
- **Future Directions**
- **Confidence Score**

---

## 🔥 Advanced Features

| Feature | Description |
|---------|-------------|
| 🤖 Multi-Agent Debate | Optimist + Skeptic perspectives merged |
| 🕸️ Citation Graph | Detects cross-citations, computes PageRank |
| 🎯 Hallucination Control | Critic agent checks every claim |
| 💾 PDF Caching | Downloads cached to avoid re-fetching |
| 📥 Download Reports | Export Markdown reports from UI |
| ⚡ LangGraph Pipeline | State-based, resumable execution |
