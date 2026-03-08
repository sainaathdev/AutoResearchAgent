"""
CLI entry point for the Autonomous Research Agent.
Allows running research from the command line without Streamlit.
"""

import argparse
import json
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table
from rich.markdown import Markdown
from rich import print as rprint

console = Console()

sys.path.insert(0, str(Path(__file__).parent))
from src.pipeline import run_research_pipeline, PIPELINE_STEPS
from src.config import OUTPUT_DIR


def print_banner():
    """Print ASCII art banner."""
    console.print(Panel.fit(
        "[bold blue]🔬 Autonomous Research Agent[/bold blue]\n"
        "[dim]Plan → Search → Filter → Extract → Compare → Debate → Report[/dim]",
        border_style="blue",
        padding=(1, 4),
    ))


def run_cli(args):
    print_banner()
    question = args.question or console.input("[bold cyan]Enter research question:[/bold cyan] ")

    if not question.strip():
        console.print("[red]Error: Research question cannot be empty.[/red]")
        sys.exit(1)

    completed_steps = []

    with Progress(
        SpinnerColumn(spinner_name="dots", style="cyan"),
        TextColumn("[bold blue]{task.description}[/bold blue]"),
        BarColumn(complete_style="green", finished_style="green"),
        TextColumn("[dim]{task.fields[status]}[/dim]"),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    ) as progress:
        main_task = progress.add_task(
            "Running Research Pipeline",
            total=len(PIPELINE_STEPS),
            status="Starting..."
        )

        def callback(node_name: str, state):
            completed_steps.append(node_name)
            done = len(completed_steps)
            step_label = next((l for n, l in PIPELINE_STEPS if n == node_name), node_name)
            progress.update(main_task, completed=done, status=f"✅ {step_label}")

        state = run_research_pipeline(
            research_question=question,
            callback=callback
        )

    # Results summary
    console.print()
    console.print(Panel.fit(
        f"[green]✅ Research Complete![/green]\n\n"
        f"📄 Papers Found: {len(state.raw_papers)}\n"
        f"✅ Papers Selected: {len(state.filtered_papers)}\n"
        f"🎯 Confidence: {state.confidence_score:.0%}\n"
        f"❌ Errors: {len(state.errors)}",
        title="[bold]Pipeline Results[/bold]",
        border_style="green"
    ))

    if state.errors:
        console.print("\n[yellow]Errors encountered:[/yellow]")
        for err in state.errors:
            console.print(f"  ⚠️  {err}")

    # Show report path
    report_files = sorted(OUTPUT_DIR.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)
    if report_files:
        latest = report_files[0]
        console.print(f"\n📁 Report saved to: [cyan]{latest}[/cyan]")

        if args.preview:
            console.print("\n" + "─" * 60)
            console.print(Markdown(state.final_report[:3000] + "\n\n...[truncated]"))

        if args.json_output:
            out = {
                "question": state.research_question,
                "papers_found": len(state.raw_papers),
                "papers_selected": len(state.filtered_papers),
                "confidence": state.confidence_score,
                "report_path": str(latest),
                "errors": state.errors,
            }
            print(json.dumps(out, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="Autonomous Research Agent — CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py -q "What are the latest advancements in diffusion models?"
  python main.py -q "Survey of RLHF methods" --preview
  python main.py -q "3D neural rendering" --json
        """
    )
    parser.add_argument("-q", "--question", type=str, help="Research question")
    parser.add_argument("--preview", action="store_true", help="Preview report in terminal")
    parser.add_argument("--json-output", action="store_true", dest="json_output",
                        help="Output results as JSON")
    args = parser.parse_args()
    run_cli(args)


if __name__ == "__main__":
    main()
