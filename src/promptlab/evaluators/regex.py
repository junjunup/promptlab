"""Regex match evaluator."""

from __future__ import annotations

import re

from promptlab.evaluators.base import BaseEvaluator, EvalContext
from promptlab.exceptions import EvaluationError
from promptlab.models import AssertionResult


class RegexEvaluator(BaseEvaluator):
    """Check if the output matches a regular expression pattern."""

    def evaluate(self, ctx: EvalContext) -> AssertionResult:
        """Evaluate regex match.

        Args:
            ctx: Evaluation context.

        Returns:
            AssertionResult indicating if output matches the regex.
        """
        pattern = ctx.assertion.value or ""

        try:
            match = re.search(pattern, ctx.output, re.IGNORECASE | re.DOTALL)
        except re.error as e:
            raise EvaluationError(f"Invalid regex pattern '{pattern}': {e}") from e

        passed = match is not None

        return AssertionResult(
            type="regex",
            passed=passed,
            expected=pattern,
            actual=ctx.output[:200],
            message="" if passed else f"Output does not match regex: '{pattern}'",
        )
