"""Evaluator registry — maps assertion types to evaluator classes."""

from __future__ import annotations

from promptlab.evaluators.base import BaseEvaluator
from promptlab.exceptions import EvaluatorNotFoundError
from promptlab.models import AssertionType


def get_evaluator_class(assertion_type: AssertionType) -> type[BaseEvaluator]:
    """Get the evaluator class for a given assertion type.

    Args:
        assertion_type: The assertion type enum.

    Returns:
        The evaluator class.

    Raises:
        EvaluatorNotFoundError: If the assertion type is unknown.
    """
    match assertion_type:
        case AssertionType.EXACT:
            from promptlab.evaluators.exact import ExactEvaluator

            return ExactEvaluator
        case AssertionType.CONTAINS:
            from promptlab.evaluators.contains import ContainsEvaluator

            return ContainsEvaluator
        case AssertionType.REGEX:
            from promptlab.evaluators.regex import RegexEvaluator

            return RegexEvaluator
        case AssertionType.JSON_VALID:
            from promptlab.evaluators.json_valid import JsonValidEvaluator

            return JsonValidEvaluator
        case AssertionType.SIMILARITY:
            from promptlab.evaluators.similarity import SimilarityEvaluator

            return SimilarityEvaluator
        case AssertionType.LLM_JUDGE:
            from promptlab.evaluators.llm_judge import LlmJudgeEvaluator

            return LlmJudgeEvaluator
        case AssertionType.COST:
            from promptlab.evaluators.cost import CostEvaluator

            return CostEvaluator
        case _:
            raise EvaluatorNotFoundError(str(assertion_type))


def create_evaluator(assertion_type: AssertionType) -> BaseEvaluator:
    """Create an evaluator instance for the given type.

    Args:
        assertion_type: The assertion type.

    Returns:
        Initialized evaluator instance.
    """
    cls = get_evaluator_class(assertion_type)
    return cls()
