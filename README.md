<div align="center">

# 🔬 AutoReAgent
### Autonomous Research Agent

**A production-grade, multi-agent AI system for autonomous academic research**

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.38%2B-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2%2B-green)](https://github.com/langchain-ai/langgraph)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-black?logo=ollama)](https://ollama.com)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

*Plan → Search → Filter → Extract → Compare → Debate → Report*

</div>

---

## 📖 Overview

**AutoReAgent** is a fully autonomous, multi-agent research system that takes a natural language research question and produces a comprehensive, structured academic report — all powered by a **local LLM via Ollama**, with zero API costs.

It searches **ArXiv** and **Semantic Scholar** for relevant papers, reads PDFs, extracts structured information, runs a multi-agent debate between an Optimist and Skeptic agent, builds a citation graph, and produces a polished Markdown report with a confidence score and hallucination check.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 **10 Specialized Agents** | Each agent handles one focused task in the pipeline |
| 🔍 **Dual Source Search** | Searches ArXiv + Semantic Scholar simultaneously |
| 📄 **PDF Extraction** | Downloads and reads full paper text automatically |
| ⚔️ **Multi-Agent Debate** | Optimist vs Skeptic agents provide balanced synthesis |
| 🕸️ **Citation Graph** | Detects cross-citations and computes PageRank influence |
| 🎯 **Hallucination Control** | Critic agent validates all claims before the final report |
| 💻 **Fully Local** | 100% offline — no OpenAI or cloud API required |
| 🖥️ **Premium UI** | Dark-themed Streamlit dashboard with live progress tracking |
| 📥 **Report Export** | Download Markdown reports and manage past reports |
| ⚡ **CLI Support** | Run headlessly from the terminal with JSON output |

---

## 🏗️ Architecture

```
User Research Question
         │
         ▼
┌─────────────────────┐
│   Research Planner  │  ← Breaks query into sub-questions & keywords
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│    Search Agent     │  ← Queries ArXiv API + Semantic Scholar API
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Filtering Agent    │  ← LLM relevance scoring per paper
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   PDF Reader Agent  │  ← Downloads PDFs, extracts full text
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Extractor Agent    │  ← Pulls methodology, datasets, metrics, limits
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Comparison Agent   │  ← Cross-paper analysis & ranking
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Debate Agent       │  ← Optimist 🆚 Skeptic → merged synthesis
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ Citation Graph Agent│  ← PageRank-based influence scoring
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Report Generator   │  ← Full structured Markdown report
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│    Critic Agent     │  ← Hallucination detection + quality score
└─────────────────────┘
         │
         ▼
   📑 Final Report
```

---

## 📁 Project Structure

```
autoReAgent/
├── app.py                      # 🖥️  Streamlit web dashboard
├── main.py                     # ⌨️  CLI entry point
├── setup_check.py              # ✅  Environment verification script
├── requirements.txt            # 📦  Python dependencies
├── .env                        # 🔑  Your environment config
├── .env.example                # 📋  Config template
│
├── .streamlit/
│   └── config.toml             # 🎨  Streamlit theme (dark mode, purple)
│
├── src/
│   ├── config.py               # ⚙️  Shared config + Pydantic models
│   ├── llm.py                  # 🧠  Ollama LLM wrapper
│   ├── pipeline.py             # 🔗  LangGraph orchestrator
│   └── agents/
│       ├── planner.py          # Research Planner Agent
│       ├── search.py           # Search Agent (ArXiv + Semantic Scholar)
│       ├── filter.py           # Paper Filtering Agent
│       ├── pdf_reader.py       # PDF Download + Extraction Agent
│       ├── extractor.py        # Information Extractor Agent
│       ├── comparison.py       # Comparative Analysis Agent
│       ├── debate.py           # Multi-Agent Debate (Optimist + Skeptic)
│       ├── citation_graph.py   # Citation Graph + PageRank
│       ├── report_generator.py # Final Report Generator
│       └── critic.py           # Quality Control / Critic Agent
│
└── data/
    ├── reports/                # 📑  Generated Markdown reports
    ├── pdf_cache/              # 💾  Cached PDFs and extracted text
    └── chroma_db/              # 🗃️  Vector store (embeddings)
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+**
- **[Ollama](https://ollama.com/download)** installed (for local LLM)
- At least **8 GB RAM** (16 GB recommended for larger models)

---

### Step 1 — Clone & set up the environment

```powershell
cd d:\sai_coding\autoReAgent

# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1

# Install all dependencies
pip install -r requirements.txt
```

---

### Step 2 — Configure environment variables

```powershell
# Copy the example config
copy .env.example .env
```

Edit `.env` and set your preferences:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3           # or mistral, llama3.2, mixtral
MAX_PAPERS_TO_PROCESS=8
RELEVANCE_THRESHOLD=0.6
SEMANTIC_SCHOLAR_API_KEY=     # optional — free at semanticscholar.org
```

---

### Step 3 — Pull an Ollama model

```powershell
# Recommended models (pick one)
ollama pull llama3        # Best balance of speed & quality
ollama pull mistral       # Faster, lighter
ollama pull llama3.2      # Latest Llama
ollama pull mixtral       # Highest quality, needs more RAM
```

---

### Step 4 — Verify setup

```powershell
python setup_check.py
```

This checks that Ollama is reachable, the model is available, and all dependencies are installed correctly.

---

### Step 5 — Run the app

**Option A — Streamlit Web UI (recommended):**

```powershell
# In terminal 1: start Ollama
ollama serve

# In terminal 2: start the app
streamlit run app.py
```

Then open **[http://localhost:8501](http://localhost:8501)** in your browser.

**Option B — Command Line Interface:**

```powershell
# Basic research query
python main.py -q "What are the latest advancements in diffusion-based video generation?"

# Preview report in terminal
python main.py -q "Survey of RLHF methods" --preview

# Output metadata as JSON
python main.py -q "3D neural scene reconstruction" --json-output
```

---

## 🎛️ Configuration Reference

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3` | LLM model to use |
| `OLLAMA_TEMPERATURE` | `0.1` | Lower = more factual output |
| `MAX_PAPERS_PER_SEARCH` | `20` | Papers fetched per query |
| `MAX_PAPERS_TO_PROCESS` | `10` | Papers fully analyzed |
| `RELEVANCE_THRESHOLD` | `0.6` | Min score (0–1) to include a paper |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence embedding model |
| `SEMANTIC_SCHOLAR_API_KEY` | *(empty)* | Optional — increases rate limits |
| `OUTPUT_DIR` | `./data/reports` | Where reports are saved |
| `PDF_CACHE_DIR` | `./data/pdf_cache` | Where PDFs are cached |

---

## 🧠 Tech Stack

| Layer | Technology |
|---|---|
| **LLM Engine** | [Ollama](https://ollama.com) — Llama 3, Mistral, Mixtral |
| **Agent Framework** | [LangGraph](https://github.com/langchain-ai/langgraph) |
| **Paper Search** | [ArXiv API](https://arxiv.org/help/api) + [Semantic Scholar API](https://api.semanticscholar.org) |
| **PDF Processing** | PyMuPDF + pdfplumber |
| **Embeddings** | SentenceTransformers (`all-MiniLM-L6-v2`) |
| **Vector Database** | ChromaDB + FAISS |
| **Graph Analysis** | NetworkX + PageRank |
| **Web UI** | Streamlit |
| **Charts** | Plotly |
| **CLI Output** | Rich |

---

## 📊 What the Report Contains

Each generated report includes:

- 📋 **Executive Summary** — key findings at a glance
- 📚 **Selected Papers Table** — with relevance scores per paper
- 🔬 **Detailed Paper Breakdowns** — methodology, datasets, metrics, limitations
- ⚖️ **Methodology Comparison** — side-by-side approach analysis
- 🏆 **Performance Ranking** — papers ranked by results
- ⚔️ **Multi-Agent Debate** — Optimist + Skeptic synthesis
- 📈 **Trend Analysis** — emerging directions in the field
- 🔭 **Research Gaps** — what's missing in current literature
- 🚀 **Future Directions** — recommended next research steps
- 🎯 **Confidence Score** — overall reliability estimate
- 🕸️ **Citation Graph** — visual influence network

Reports are saved as `.md` files in `data/reports/` and can be downloaded directly from the UI.

---

## �️ UI Features

The Streamlit dashboard includes:

- **One-click example questions** to instantly start a research run
- **Live pipeline progress** with per-agent status tracking
- **6 result tabs**: Report · Papers · Analysis · Debate · Citation Graph · Critic
- **Past Reports manager** — open or delete previous reports from the sidebar
- **Model selector** — switch between Ollama models from the UI
- **Configurable sliders** — adjust paper count and relevance threshold live

---

## 🤖 Supported Ollama Models

| Model | RAM Required | Speed | Quality |
|---|---|---|---|
| `llama3` | ~6 GB | ⚡⚡⚡ | ★★★★ |
| `llama3.2` | ~4 GB | ⚡⚡⚡⚡ | ★★★★ |
| `mistral` | ~5 GB | ⚡⚡⚡⚡ | ★★★☆ |
| `mixtral` | ~26 GB | ⚡⚡ | ★★★★★ |
| `deepseek-coder` | ~8 GB | ⚡⚡⚡ | ★★★☆ |

---

## ❓ Troubleshooting

**Ollama not reachable**
```powershell
ollama serve   # Run this in a separate terminal
```

**Model not found**
```powershell
ollama pull llama3   # Pull the model first
```

**Dependencies missing**
```powershell
pip install -r requirements.txt --upgrade
```

**Port already in use**
```powershell
streamlit run app.py --server.port 8502
```

**Run the setup checker** for a full diagnostic:
```powershell
python setup_check.py
```

---

## 📄 License

This project is licensed under the **MIT License** — free to use, modify, and distribute.

---

<div align="center">

Built with ❤️ using **LangGraph · Ollama · Streamlit**

*100% local · No cloud APIs · No data leaves your machine*

</div>
