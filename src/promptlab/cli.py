"""PromptLab CLI — powered by Typer."""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer(
    name="promptlab",
    help="🧪 PromptLab — A lightweight LLM evaluation toolkit.",
    add_completion=False,
    no_args_is_help=True,
)
console = Console()


@app.command()
def run(
    config_path: str = typer.Argument(
        ...,
        help="Path to the YAML evaluation config file.",
    ),
    output: str = typer.Option(
        None,
        "--output",
        "-o",
        help="Override output file path.",
    ),
    output_format: str = typer.Option(
        "json",
        "--format",
        "-f",
        help="Output format: json or csv.",
    ),
    provider: str | None = typer.Option(
        None,
        "--provider",
        "-p",
        help="Only run with the specified provider ID.",
    ),
) -> None:
    """Run an evaluation from a YAML config file."""
    from promptlab.config import load_config
    from promptlab.exceptions import ConfigError, PromptLabError
    from promptlab.reporters import ConsoleReporter, CsvReporter, JsonReporter
    from promptlab.runner import Runner

    reporter = ConsoleReporter()

    try:
        config = load_config(config_path)
    except ConfigError as e:
        reporter.print_error(str(e))
        raise typer.Exit(code=1) from e

    # Filter providers if specified
    if provider:
        config.providers = [p for p in config.providers if p.id == provider]
        if not config.providers:
            reporter.print_error(f"Provider '{provider}' not found in config.")
            raise typer.Exit(code=1)

    # Print header
    reporter.print_header(
        config_path=config_path,
        num_providers=len(config.providers),
        num_prompts=len(config.prompts),
        num_tests=len(config.tests),
    )

    # Run the evaluation
    runner = Runner(config, config_path=config_path)
    try:
        results = asyncio.run(runner.run())
    except PromptLabError as e:
        reporter.print_error(str(e))
        raise typer.Exit(code=1) from e

    # Print console report
    reporter.print_results(results)

    # Save results to file
    output_path = output or config.settings.output
    if output_path:
        fmt = output_format.lower()
        if fmt == "csv":
            saved = CsvReporter().save(results, output_path)
        else:
            saved = JsonReporter().save(results, output_path)
        console.print(f"\n💾 Results saved to: [bold]{saved}[/]\n")

    # Exit with error code if any tests failed
    if results.get("total_failed", 0) > 0:
        raise typer.Exit(code=1)


@app.command()
def init(
    output: str = typer.Option(
        "eval.yaml",
        "--output",
        "-o",
        help="Output file path for the example config.",
    ),
) -> None:
    """Generate an example evaluation config file."""
    from promptlab.config import generate_example_config

    path = Path(output)
    if path.exists():
        overwrite = typer.confirm(f"'{output}' already exists. Overwrite?")
        if not overwrite:
            console.print("[yellow]Aborted.[/]")
            raise typer.Exit()

    path.write_text(generate_example_config(), encoding="utf-8")
    console.print(f"\n✅ Example config created: [bold]{output}[/]")
    console.print(f"   Edit it, then run: [cyan]promptlab run {output}[/]\n")


@app.command()
def version() -> None:
    """Show PromptLab version."""
    from promptlab import __version__

    console.print(f"🧪 PromptLab v{__version__}")


if __name__ == "__main__":
    app()
