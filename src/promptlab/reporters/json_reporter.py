"""JSON file reporter."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class JsonReporter:
    """Export evaluation results to a JSON file."""

    def save(self, data: dict[str, Any], output_path: str) -> str:
        """Save results to a JSON file.

        Args:
            data: Evaluation results dictionary.
            output_path: Path to the output file.

        Returns:
            Absolute path to the saved file.
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

        return str(path.resolve())
