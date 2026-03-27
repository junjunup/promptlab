"""Contains evaluator."""

from __future__ import annotations

from promptlab.evaluators.base import BaseEvaluator, EvalContext
from promptlab.models import AssertionResult


class ContainsEvaluator(BaseEvaluator):
    """Check if the output contains the expected substring."""

    def evaluate(self, ctx: EvalContext) -> AssertionResult:
        """Evaluate substring containment (case-insensitive).

        Args:
            ctx: Evaluation context.

        Returns:
            AssertionResult indicating if output contains expected value.
        """
        expected = ctx.assertion.value or ""
        output_lower = ctx.output.lower()
        expected_lower = expected.lower()
        passed = expected_lower in output_lower

        return AssertionResult(
            type="contains",
            passed=passed,
            expected=expected,
            actual=ctx.output[:200],
            message="" if passed else f"Output does not contain: '{expected}'",
        )
