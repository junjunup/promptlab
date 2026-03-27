"""Rich console reporter — colorful terminal output."""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


class ConsoleReporter:
    """Render evaluation results as colorful terminal output using Rich."""

    def __init__(self) -> None:
        self.console = Console()

    def print_header(
        self, config_path: str, num_providers: int, num_prompts: int, num_tests: int
    ) -> None:
        """Print the evaluation header.

        Args:
            config_path: Path to the config file.
            num_providers: Number of providers.
            num_prompts: Number of prompts.
            num_tests: Number of test cases.
        """
        total = num_providers * num_prompts * num_tests

        from promptlab import __version__

        self.console.print()
        self.console.print(
            f"[bold cyan]🧪 PromptLab v{__version__}[/] — Running evaluation...",
        )
        self.console.print()
        self.console.print(f"  📋 Config:     [bold]{config_path}[/]")
        self.console.print(f"  🤖 Providers:  {num_providers}")
        self.console.print(f"  📝 Prompts:    {num_prompts}")
        self.console.print(f"  🧪 Tests:      {num_tests}")
        self.console.print(f"  📊 Total:      [bold]{total}[/] evaluations")
        self.console.print()

    def print_results(self, data: dict[str, Any]) -> None:
        """Print the results matrix and summaries.

        Args:
            data: Evaluation results dictionary (from EvalRunResult.model_dump()).
        """
        results = data.get("results", [])
        summaries = data.get("provider_summaries", [])

        if not results:
            self.console.print("[yellow]No results to display.[/]")
            return

        # Group results by provider for separate tables
        provider_groups: dict[str, list[dict[str, Any]]] = {}
        for r in results:
            pid = r["provider_id"]
            provider_groups.setdefault(pid, []).append(r)

        # Get unique prompt IDs
        prompt_ids = sorted({r["prompt_id"] for r in results})

        for provider_id, provider_results in provider_groups.items():
            # Build results matrix table
            table = Table(
                title=f"📊 Results — [bold]{provider_id}[/]",
                show_lines=True,
                expand=True,
            )
            table.add_column("Test Case", style="white", max_width=40)
            for pid in prompt_ids:
                table.add_column(pid, justify="center")

            # Group by test index
            test_groups: dict[int, dict[str, dict[str, Any]]] = {}
            for r in provider_results:
                tidx = r["test_index"]
                pid = r["prompt_id"]
                test_groups.setdefault(tidx, {})[pid] = r

            for _tidx, prompts in sorted(test_groups.items()):
                row: list[str | Text] = []
                # Use first prompt's description for the test name
                first_result = next(iter(prompts.values()))
                desc = first_result.get("test_description", "")
                if desc and len(desc) > 37:
                    desc = desc[:37] + "..."
                row.append(desc or f"Test #{_tidx + 1}")

                for pid in prompt_ids:
                    r = prompts.get(pid)
                    if r is None:
                        row.append("—")
                    elif r.get("error"):
                        row.append(Text("⚠ ERROR", style="bold yellow"))
                    elif r["passed"]:
                        row.append(Text("✅ PASS", style="bold green"))
                    else:
                        row.append(Text("❌ FAIL", style="bold red"))

                table.add_row(*row)

            # Add pass rate footer
            pass_rate_row: list[str | Text] = [Text("Pass Rate", style="bold")]
            for pid in prompt_ids:
                pid_results = [r for r in provider_results if r["prompt_id"] == pid]
                passed = sum(1 for r in pid_results if r["passed"])
                rate = passed / len(pid_results) if pid_results else 0
                color = "green" if rate >= 0.8 else "yellow" if rate >= 0.5 else "red"
                pass_rate_row.append(Text(f"{rate:.0%}", style=f"bold {color}"))
            table.add_row(*pass_rate_row)

            self.console.print(table)
            self.console.print()

        # Cost summary
        total_cost = data.get("total_cost_usd", 0)
        if summaries:
            self.console.print("[bold]💰 Cost Summary[/]")
            for s in summaries:
                tokens = s.get("total_tokens", 0)
                cost = s.get("total_cost_usd", 0)
                latency = s.get("avg_latency_ms", 0)
                self.console.print(
                    f"   {s['provider_id']:12s}  "
                    f"${cost:.4f}  ({tokens:,} tokens, "
                    f"avg {latency:.0f}ms)"
                )
            self.console.print(f"   {'Total':12s}  [bold]${total_cost:.4f}[/]")
            self.console.print()

        # Final verdict
        total_tests = data.get("total_tests", 0)
        total_passed = data.get("total_passed", 0)
        total_failed = data.get("total_failed", 0)
        rate = data.get("overall_pass_rate", 0)
        duration = data.get("total_duration_ms", 0)

        if rate >= 0.8:
            emoji = "✅"
            style = "bold green"
        elif rate >= 0.5:
            emoji = "⚠️"
            style = "bold yellow"
        else:
            emoji = "❌"
            style = "bold red"

        self.console.print(
            Panel(
                f"{emoji} [bold]{total_passed}/{total_tests} passed[/] "
                f"({total_failed} failed) — [{style}]{rate:.0%}[/] pass rate\n"
                f"⏱  Completed in {duration / 1000:.1f}s",
                title="Evaluation Complete",
                border_style="cyan",
            )
        )

    def print_error(self, message: str) -> None:
        """Print an error message.

        Args:
            message: Error message to display.
        """
        self.console.print(f"\n[bold red]❌ Error:[/] {message}\n")
