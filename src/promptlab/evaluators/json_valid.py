"""JSON validation evaluator."""

from __future__ import annotations

import json

from promptlab.evaluators.base import BaseEvaluator, EvalContext
from promptlab.models import AssertionResult


def _extract_json_from_codeblock(text: str) -> str:
    """Safely extract JSON from markdown code blocks.

    Handles: ```json ... ```, ``` ... ```, and plain text.
    """
    # Try ```json block first
    marker = "```json"
    start = text.find(marker)
    if start != -1:
        start += len(marker)
        end = text.find("```", start)
        if end != -1:
            return text[start:end].strip()

    # Try plain ``` block
    marker = "```"
    start = text.find(marker)
    if start != -1:
        start += len(marker)
        end = text.find("```", start)
        if end != -1:
            return text[start:end].strip()

    return text


class JsonValidEvaluator(BaseEvaluator):
    """Check if the output is valid JSON."""

    def evaluate(self, ctx: EvalContext) -> AssertionResult:
        """Evaluate JSON validity.

        Args:
            ctx: Evaluation context.

        Returns:
            AssertionResult indicating if output is valid JSON.
        """
        output = ctx.output.strip()

        # Try to extract JSON from markdown code blocks (safe extraction)
        output = _extract_json_from_codeblock(output)

        try:
            parsed = json.loads(output)
            passed = True
            message = ""

            # If a value is specified, check if parsed JSON matches
            if ctx.assertion.value:
                try:
                    expected = json.loads(ctx.assertion.value)
                    if parsed != expected:
                        passed = False
                        message = "JSON is valid but does not match expected value"
                except json.JSONDecodeError:
                    # value is not JSON, check if it's a key that should exist
                    if isinstance(parsed, dict) and ctx.assertion.value not in parsed:
                        passed = False
                        message = (
                            f"JSON key '{ctx.assertion.value}' not found in output"
                        )

        except json.JSONDecodeError as e:
            passed = False
            message = f"Invalid JSON: {e}"

        return AssertionResult(
            type="json_valid",
            passed=passed,
            expected=ctx.assertion.value,
            actual=output[:200],
            message=message,
        )
