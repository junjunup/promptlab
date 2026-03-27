"""Cost limit evaluator."""

from __future__ import annotations

from promptlab.evaluators.base import BaseEvaluator, EvalContext
from promptlab.models import AssertionResult


class CostEvaluator(BaseEvaluator):
    """Check if the token usage is within limits.

    Uses max_tokens from the assertion config to set the ceiling.
    """

    def evaluate(self, ctx: EvalContext) -> AssertionResult:
        """Evaluate token usage against limit.

        Note: This evaluator is special — it checks metadata set by
        the Runner after the LLM call, not the output text itself.
        The `output` field is expected to contain the total token count
        as a string (set by the Runner).

        Args:
            ctx: Evaluation context. output = total tokens as string.

        Returns:
            AssertionResult indicating if within cost limits.
        """
        max_tokens = ctx.assertion.max_tokens or 500

        try:
            actual_tokens = int(ctx.output)
        except (ValueError, TypeError):
            return AssertionResult(
                type="cost",
                passed=True,
                message="Token count not available, skipping cost check",
            )

        passed = actual_tokens <= max_tokens

        return AssertionResult(
            type="cost",
            passed=passed,
            expected=f"≤{max_tokens} tokens",
            actual=f"{actual_tokens} tokens",
            message=""
            if passed
            else (f"Token usage {actual_tokens} exceeds limit {max_tokens}"),
        )
