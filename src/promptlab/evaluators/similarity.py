"""Text similarity evaluator."""

from __future__ import annotations

import difflib

from promptlab.evaluators.base import BaseEvaluator, EvalContext
from promptlab.models import AssertionResult

_DEFAULT_THRESHOLD = 0.8


class SimilarityEvaluator(BaseEvaluator):
    """Check if the output is similar enough to the expected value.

    Uses difflib.SequenceMatcher for text similarity scoring.
    """

    def evaluate(self, ctx: EvalContext) -> AssertionResult:
        """Evaluate text similarity.

        Args:
            ctx: Evaluation context.

        Returns:
            AssertionResult with similarity score.
        """
        expected = ctx.assertion.value or ""
        threshold = ctx.assertion.threshold or _DEFAULT_THRESHOLD
        output = ctx.output.strip()

        # Use difflib for basic similarity
        score = difflib.SequenceMatcher(None, output.lower(), expected.lower()).ratio()

        passed = score >= threshold

        return AssertionResult(
            type="similarity",
            passed=passed,
            expected=f"≥{threshold:.0%} similar to: '{expected[:50]}'",
            actual=f"{score:.1%} similarity",
            message=""
            if passed
            else f"Similarity {score:.1%} < threshold {threshold:.0%}",
            score=round(score, 4),
        )
