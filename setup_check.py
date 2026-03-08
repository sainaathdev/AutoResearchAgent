"""
Setup script for the Autonomous Research Agent.
Verifies Ollama is running and the model is available.
"""

import subprocess
import sys
import importlib
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def check_package(name: str, import_name: str | None = None) -> bool:
    try:
        importlib.import_module(import_name or name)
        return True
    except ImportError:
        return False


def check_ollama() -> tuple[bool, list[str]]:
    """Check if Ollama is running and list available models."""
    try:
        import requests
        resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        if resp.status_code == 200:
            models = [m["name"] for m in resp.json().get("models", [])]
            return True, models
        return False, []
    except Exception:
        return False, []


def main():
    console.print(Panel.fit(
        "[bold blue]🔬 Autonomous Research Agent — Setup Check[/bold blue]",
        border_style="blue"
    ))

    # ── Package Checks ──
    console.print("\n[bold]📦 Checking Python packages...[/bold]\n")

    packages = [
        ("langchain", None),
        ("langchain_community", None),
        ("langchain_ollama", None),
        ("langgraph", None),
        ("arxiv", None),
        ("requests", None),  # for semanticscholar
        ("fitz", "PyMuPDF"),
        ("pdfplumber", None),
        ("sentence_transformers", None),
        ("chromadb", None),
        ("streamlit", None),
        ("plotly", None),
        ("networkx", None),
        ("pandas", None),
        ("rich", None),
        ("loguru", None),
        ("pydantic", None),
        ("tenacity", None),
    ]

    table = Table(show_header=True, header_style="bold blue", border_style="dim")
    table.add_column("Package", style="white")
    table.add_column("Status", justify="center")

    all_ok = True
    for pkg, display in packages:
        import_name = pkg
        ok = check_package(import_name)
        status = "[green]✅ OK[/green]" if ok else "[red]❌ Missing[/red]"
        if not ok:
            all_ok = False
        table.add_row(display or pkg, status)

    console.print(table)

    # ── Ollama Check ──
    console.print("\n[bold]🤖 Checking Ollama...[/bold]\n")
    ollama_running, models = check_ollama()

    if ollama_running:
        console.print(f"[green]✅ Ollama is running[/green]")
        if models:
            console.print(f"[dim]Available models: {', '.join(models)}[/dim]")
            if any("llama" in m for m in models):
                console.print("[green]✅ LLaMA model detected[/green]")
            else:
                console.print("[yellow]⚠️  No LLaMA model found. Run: ollama pull llama3.2[/yellow]")
        else:
            console.print("[yellow]⚠️  No models installed. Run: ollama pull llama3.2[/yellow]")
    else:
        console.print("[red]❌ Ollama not running.[/red]")
        console.print("[dim]Start with: ollama serve[/dim]")
        console.print("[dim]Install from: https://ollama.ai[/dim]")

    # ── Directory Check ──
    console.print("\n[bold]📁 Checking directories...[/bold]\n")
    dirs = [
        Path("data/reports"),
        Path("data/pdf_cache"),
        Path("data/chroma_db"),
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        console.print(f"[green]✅[/green] {d}")

    # ── Summary ──
    console.print()
    if all_ok and ollama_running and models:
        console.print(Panel.fit(
            "[bold green]✅ All checks passed! Ready to run.[/bold green]\n\n"
            "Start the UI:    [cyan]streamlit run app.py[/cyan]\n"
            "Use the CLI:     [cyan]python main.py -q 'your question'[/cyan]",
            border_style="green"
        ))
    else:
        console.print(Panel.fit(
            "[bold yellow]⚠️  Some checks failed.[/bold yellow]\n\n"
            "Install packages:  [cyan].\\venv\\Scripts\\pip install -r requirements.txt[/cyan]\n"
            "Start Ollama:      [cyan]ollama serve[/cyan]\n"
            "Pull model:        [cyan]ollama pull llama3.2[/cyan]",
            border_style="yellow"
        ))


if __name__ == "__main__":
    main()
