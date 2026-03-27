"""Pydantic data models for PromptLab configuration and results."""

from __future__ import annotations

import time
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ─── Configuration Models ───────────────────────────────────────────


class ProviderType(str, Enum):
    """Supported LLM provider types."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"


class ProviderConfig(BaseModel):
    """Configuration for a single LLM provider."""

    id: str
    type: ProviderType
    model: str
    temperature: float = 0.0
    max_tokens: int = 1024
    api_key: str | None = None
    base_url: str | None = None


class PromptConfig(BaseModel):
    """Configuration for a single prompt template."""

    id: str
    content: str


class AssertionType(str, Enum):
    """Built-in assertion/evaluator types."""

    EXACT = "exact"
    CONTAINS = "contains"
    REGEX = "regex"
    JSON_VALID = "json_valid"
    SIMILARITY = "similarity"
    LLM_JUDGE = "llm_judge"
    COST = "cost"


class AssertionConfig(BaseModel):
    """Configuration for a single assertion on an LLM output."""

    type: AssertionType
    value: str | None = None
    threshold: float | None = None
    max_tokens: int | None = None
    judge_prompt: str | None = None
    judge_provider: str | None = None


class TestCaseConfig(BaseModel):
    """Configuration for a single test case."""

    __test__ = False  # Prevent pytest from collecting this class

    description: str | None = None
    vars: dict[str, str] = Field(default_factory=dict)
    assert_: list[AssertionConfig] = Field(default_factory=list, alias="assert")

    model_config = {"populate_by_name": True}


class EvalSettings(BaseModel):
    """Global evaluation settings."""

    concurrency: int = 5
    timeout: int = 30
    output: str | None = None
    output_format: str = "json"


class EvalConfig(BaseModel):
    """Top-level evaluation configuration (parsed from YAML)."""

    description: str = ""
    providers: list[ProviderConfig]
    prompts: list[PromptConfig]
    tests: list[TestCaseConfig]
    settings: EvalSettings = Field(default_factory=EvalSettings)


# ─── Result Models ──────────────────────────────────────────────────


class AssertionResult(BaseModel):
    """Result of a single assertion."""

    type: str
    passed: bool
    expected: str | None = None
    actual: str | None = None
    message: str = ""
    score: float | None = None


class TestResult(BaseModel):
    """Result of a single test case evaluation."""

    test_index: int
    test_description: str | None = None
    provider_id: str
    prompt_id: str
    prompt_rendered: str
    output: str
    assertions: list[AssertionResult]
    passed: bool
    latency_ms: float = 0.0
    token_usage: TokenUsage | None = None
    error: str | None = None


class TokenUsage(BaseModel):
    """Token usage information for a single LLM call."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0


class ProviderSummary(BaseModel):
    """Summary statistics for a single provider."""

    provider_id: str
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    pass_rate: float = 0.0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    avg_latency_ms: float = 0.0


class EvalRunResult(BaseModel):
    """Complete evaluation run result."""

    run_id: str
    description: str = ""
    timestamp: float = Field(default_factory=time.time)
    config_path: str = ""
    results: list[TestResult] = Field(default_factory=list)
    provider_summaries: list[ProviderSummary] = Field(default_factory=list)
    total_tests: int = 0
    total_passed: int = 0
    total_failed: int = 0
    overall_pass_rate: float = 0.0
    total_cost_usd: float = 0.0
    total_duration_ms: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


# Rebuild models to resolve forward references
TestResult.model_rebuild()
