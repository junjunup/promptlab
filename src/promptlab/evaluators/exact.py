"""Exact match evaluator."""

from __future__ import annotations

from promptlab.evaluators.base import BaseEvaluator, EvalContext
from promptlab.models import AssertionResult


class ExactEvaluator(BaseEvaluator):
    """Check if the output exactly matches the expected value."""

    def evaluate(self, ctx: EvalContext) -> AssertionResult:
        """Evaluate exact match.

        Args:
            ctx: Evaluation context.

        Returns:
            AssertionResult indicating if output matches expected value.
        """
        expected = ctx.assertion.value or ""
        output = ctx.output.strip()
        passed = output == expected

        return AssertionResult(
            type="exact",
            passed=passed,
            expected=expected,
            actual=output,
            message="" if passed else f"Expected exact match: '{expected}'",
        )
