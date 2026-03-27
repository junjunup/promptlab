"""PromptLab — A lightweight, YAML-driven LLM evaluation toolkit for Python."""

from __future__ import annotations

__version__ = "0.1.0"
__all__ = [
    "EvalConfig",
    "PromptLabError",
    "run_evaluation",
]

from promptlab.exceptions import PromptLabError
from promptlab.models import EvalConfig


def run_evaluation(config_path: str, **kwargs: object) -> dict[str, object]:
    """Run an evaluation from a YAML config file.

    This is the main programmatic entry point for PromptLab.

    Args:
        config_path: Path to the YAML evaluation config file.
        **kwargs: Override config settings.

    Returns:
        Evaluation results dictionary.
    """
    from promptlab.config import load_config
    from promptlab.runner import Runner

    config = load_config(config_path, **kwargs)
    runner = Runner(config, config_path=config_path)
    import asyncio

    return asyncio.run(runner.run())
