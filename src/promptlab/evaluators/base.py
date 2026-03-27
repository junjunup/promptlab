"""Base class for evaluators."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from promptlab.models import AssertionConfig, AssertionResult


@dataclass
class EvalContext:
    """Context passed to evaluators during assertion evaluation."""

    output: str
    assertion: AssertionConfig
    prompt_rendered: str = ""
    variables: dict[str, str] | None = None


class BaseEvaluator(ABC):
    """Abstract base class for evaluators.

    All evaluator implementations must inherit from this class
    and implement the `evaluate` method.
    """

    @abstractmethod
    def evaluate(self, ctx: EvalContext) -> AssertionResult:
        """Evaluate the LLM output against the assertion.

        Args:
            ctx: Evaluation context with output and assertion config.

        Returns:
            AssertionResult with pass/fail status and details.
        """

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"
