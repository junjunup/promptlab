"""Shared test fixtures for PromptLab tests."""

from __future__ import annotations

import pytest

from promptlab.models import (
    AssertionConfig,
    AssertionType,
    EvalConfig,
    EvalSettings,
    PromptConfig,
    ProviderConfig,
    ProviderType,
    TestCaseConfig,
)


@pytest.fixture
def basic_config() -> EvalConfig:
    """Create a basic evaluation config for testing."""
    return EvalConfig(
        description="Test evaluation",
        providers=[
            ProviderConfig(
                id="test-provider",
                type=ProviderType.OPENAI,
                model="gpt-4o-mini",
                temperature=0.0,
            ),
        ],
        prompts=[
            PromptConfig(id="v1", content="Answer: {{question}}"),
        ],
        tests=[
            TestCaseConfig(
                vars={"question": "What is 2+2?"},
                **{
                    "assert": [
                        AssertionConfig(type=AssertionType.CONTAINS, value="4"),
                    ]
                },
            ),
        ],
        settings=EvalSettings(concurrency=1, timeout=10),
    )


@pytest.fixture
def multi_provider_config() -> EvalConfig:
    """Create a multi-provider evaluation config for testing."""
    return EvalConfig(
        description="Multi-provider test",
        providers=[
            ProviderConfig(
                id="provider-a",
                type=ProviderType.OPENAI,
                model="gpt-4o-mini",
            ),
            ProviderConfig(
                id="provider-b",
                type=ProviderType.ANTHROPIC,
                model="claude-3-5-haiku-20241022",
            ),
        ],
        prompts=[
            PromptConfig(id="v1", content="Q: {{question}}"),
            PromptConfig(id="v2", content="Answer briefly: {{question}}"),
        ],
        tests=[
            TestCaseConfig(
                vars={"question": "Capital of France?"},
                **{
                    "assert": [
                        AssertionConfig(type=AssertionType.CONTAINS, value="Paris"),
                    ]
                },
            ),
        ],
        settings=EvalSettings(concurrency=2),
    )


@pytest.fixture
def sample_yaml_content() -> str:
    """Return valid YAML config content for file-based tests."""
    return """\
description: "Test config"

providers:
  - id: test
    type: openai
    model: gpt-4o-mini
    temperature: 0

prompts:
  - id: v1
    content: "Answer: {{question}}"

tests:
  - vars:
      question: "What is 2+2?"
    assert:
      - type: contains
        value: "4"

settings:
  concurrency: 1
  timeout: 10
"""
