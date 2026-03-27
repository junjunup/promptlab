"""YAML configuration loader and validator."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from promptlab.exceptions import ConfigError
from promptlab.models import EvalConfig


def load_config(config_path: str, **overrides: Any) -> EvalConfig:
    """Load and validate an evaluation config from a YAML file.

    Args:
        config_path: Path to the YAML config file.
        **overrides: Optional overrides for config settings.

    Returns:
        Validated EvalConfig instance.

    Raises:
        ConfigError: If the file cannot be read or the config is invalid.
    """
    path = Path(config_path)
    if not path.exists():
        raise ConfigError(f"Config file not found: {config_path}")
    if path.suffix.lower() not in (".yaml", ".yml"):
        raise ConfigError(f"Config file must be .yaml or .yml, got: {path.suffix}")

    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as e:
        raise ConfigError(f"Cannot read config file: {e}") from e

    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML syntax: {e}") from e

    if not isinstance(data, dict):
        raise ConfigError("Config file must contain a YAML mapping (dict)")

    # Resolve environment variables in API keys
    data = _resolve_env_vars(data)

    # Apply overrides
    if overrides:
        settings = data.get("settings", {})
        settings.update(overrides)
        data["settings"] = settings

    try:
        config = EvalConfig.model_validate(data)
    except Exception as e:
        raise ConfigError(f"Config validation failed: {e}") from e

    _validate_config_semantics(config)

    return config


def _resolve_env_vars(data: Any) -> Any:
    """Recursively resolve ${ENV_VAR} patterns in string values."""
    if isinstance(data, str):
        if data.startswith("${") and data.endswith("}"):
            env_key = data[2:-1]
            value = os.environ.get(env_key)
            if value is None:
                raise ConfigError(f"Environment variable '{env_key}' is not set")
            return value
        return data
    if isinstance(data, dict):
        return {k: _resolve_env_vars(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_resolve_env_vars(item) for item in data]
    return data


def _validate_config_semantics(config: EvalConfig) -> None:
    """Validate semantic correctness beyond schema validation."""
    if not config.providers:
        raise ConfigError("At least one provider is required")
    if not config.prompts:
        raise ConfigError("At least one prompt is required")
    if not config.tests:
        raise ConfigError("At least one test case is required")

    # Check for duplicate provider IDs
    provider_ids = [p.id for p in config.providers]
    if len(provider_ids) != len(set(provider_ids)):
        raise ConfigError("Duplicate provider IDs found")

    # Check for duplicate prompt IDs
    prompt_ids = [p.id for p in config.prompts]
    if len(prompt_ids) != len(set(prompt_ids)):
        raise ConfigError("Duplicate prompt IDs found")

    # Validate LLM judge references
    for test in config.tests:
        for assertion in test.assert_:
            if (
                assertion.type.value == "llm_judge"
                and assertion.judge_provider
                and assertion.judge_provider not in provider_ids
            ):
                raise ConfigError(
                    f"LLM judge references unknown provider: "
                    f"'{assertion.judge_provider}'"
                )


def generate_example_config() -> str:
    """Generate an example YAML config string.

    Returns:
        Example YAML configuration content.
    """
    return """\
# PromptLab Evaluation Config
# Run with: promptlab run eval.yaml

description: "My first prompt evaluation"

providers:
  - id: gpt4
    type: openai
    model: gpt-4o-mini
    temperature: 0

prompts:
  - id: v1
    content: |
      Answer the following question concisely.
      Question: {{question}}

tests:
  - vars:
      question: "What is the capital of France?"
    assert:
      - type: contains
        value: "Paris"
  - vars:
      question: "What is 2 + 2?"
    assert:
      - type: contains
        value: "4"
  - vars:
      question: "Is the sky blue?"
    assert:
      - type: contains
        value: "yes"

settings:
  concurrency: 3
  timeout: 30
  output: results/eval_results.json
"""
