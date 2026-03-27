"""CSV file reporter."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


class CsvReporter:
    """Export evaluation results to a CSV file."""

    def save(self, data: dict[str, Any], output_path: str) -> str:
        """Save results to a CSV file.

        Args:
            data: Evaluation results dictionary.
            output_path: Path to the output file.

        Returns:
            Absolute path to the saved file.
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        results = data.get("results", [])
        if not results:
            path.write_text("No results\n", encoding="utf-8")
            return str(path.resolve())

        fieldnames = [
            "test_index",
            "test_description",
            "provider_id",
            "prompt_id",
            "output",
            "passed",
            "latency_ms",
            "total_tokens",
            "cost_usd",
            "assertions_summary",
            "error",
        ]

        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for r in results:
                token_usage = r.get("token_usage") or {}
                assertions = r.get("assertions", [])
                assertions_summary = "; ".join(
                    f"{a['type']}:{'PASS' if a['passed'] else 'FAIL'}"
                    for a in assertions
                )

                writer.writerow(
                    {
                        "test_index": r.get("test_index", ""),
                        "test_description": r.get("test_description", ""),
                        "provider_id": r.get("provider_id", ""),
                        "prompt_id": r.get("prompt_id", ""),
                        "output": r.get("output", "")[:200],
                        "passed": r.get("passed", False),
                        "latency_ms": f"{r.get('latency_ms', 0):.0f}",
                        "total_tokens": token_usage.get("total_tokens", 0),
                        "cost_usd": f"{token_usage.get('estimated_cost_usd', 0):.6f}",
                        "assertions_summary": assertions_summary,
                        "error": r.get("error", ""),
                    }
                )

        return str(path.resolve())
