"""Tests for evaluators."""

from __future__ import annotations

import pytest

from promptlab.evaluators.base import EvalContext
from promptlab.evaluators.contains import ContainsEvaluator
from promptlab.evaluators.cost import CostEvaluator
from promptlab.evaluators.exact import ExactEvaluator
from promptlab.evaluators.json_valid import JsonValidEvaluator
from promptlab.evaluators.regex import RegexEvaluator
from promptlab.evaluators.registry import create_evaluator, get_evaluator_class
from promptlab.evaluators.similarity import SimilarityEvaluator
from promptlab.evaluators.llm_judge import LlmJudgeEvaluator
from promptlab.exceptions import EvaluationError, EvaluatorNotFoundError
from promptlab.models import AssertionConfig, AssertionType


def _ctx(
    output: str,
    value: str | None = None,
    threshold: float | None = None,
    max_tokens: int | None = None,
    assertion_type: AssertionType = AssertionType.CONTAINS,
) -> EvalContext:
    """Helper to create an EvalContext."""
    return EvalContext(
        output=output,
        assertion=AssertionConfig(
            type=assertion_type,
            value=value,
            threshold=threshold,
            max_tokens=max_tokens,
        ),
    )


class TestExactEvaluator:
    """Tests for exact match evaluator."""

    def test_exact_match_pass(self) -> None:
        result = ExactEvaluator().evaluate(
            _ctx("hello", "hello", assertion_type=AssertionType.EXACT)
        )
        assert result.passed is True

    def test_exact_match_fail(self) -> None:
        result = ExactEvaluator().evaluate(
            _ctx("hello world", "hello", assertion_type=AssertionType.EXACT)
        )
        assert result.passed is False

    def test_exact_match_strips_whitespace(self) -> None:
        result = ExactEvaluator().evaluate(
            _ctx("  hello  ", "hello", assertion_type=AssertionType.EXACT)
        )
        assert result.passed is True

    def test_exact_match_empty(self) -> None:
        result = ExactEvaluator().evaluate(
            _ctx("", "", assertion_type=AssertionType.EXACT)
        )
        assert result.passed is True


class TestContainsEvaluator:
    """Tests for contains evaluator."""

    def test_contains_pass(self) -> None:
        result = ContainsEvaluator().evaluate(_ctx("The answer is Paris", "Paris"))
        assert result.passed is True

    def test_contains_fail(self) -> None:
        result = ContainsEvaluator().evaluate(_ctx("The answer is London", "Paris"))
        assert result.passed is False

    def test_contains_case_insensitive(self) -> None:
        result = ContainsEvaluator().evaluate(_ctx("POSITIVE sentiment", "positive"))
        assert result.passed is True

    def test_contains_empty_value(self) -> None:
        result = ContainsEvaluator().evaluate(_ctx("anything", ""))
        assert result.passed is True

    def test_contains_chinese(self) -> None:
        result = ContainsEvaluator().evaluate(_ctx("这是一个积极的评价", "积极"))
        assert result.passed is True


class TestRegexEvaluator:
    """Tests for regex evaluator."""

    def test_regex_pass(self) -> None:
        result = RegexEvaluator().evaluate(
            _ctx("Answer: 42", r"Answer:\s*\d+", assertion_type=AssertionType.REGEX)
        )
        assert result.passed is True

    def test_regex_fail(self) -> None:
        result = RegexEvaluator().evaluate(
            _ctx("No numbers here", r"\d+", assertion_type=AssertionType.REGEX)
        )
        assert result.passed is False

    def test_regex_case_insensitive(self) -> None:
        result = RegexEvaluator().evaluate(
            _ctx("PASS", r"pass", assertion_type=AssertionType.REGEX)
        )
        assert result.passed is True

    def test_regex_invalid_pattern(self) -> None:
        with pytest.raises(EvaluationError, match="Invalid regex"):
            RegexEvaluator().evaluate(
                _ctx("test", r"[invalid", assertion_type=AssertionType.REGEX)
            )


class TestJsonValidEvaluator:
    """Tests for JSON validation evaluator."""

    def test_valid_json(self) -> None:
        result = JsonValidEvaluator().evaluate(
            _ctx(
                '{"name": "Alice", "age": 30}', assertion_type=AssertionType.JSON_VALID
            )
        )
        assert result.passed is True

    def test_invalid_json(self) -> None:
        result = JsonValidEvaluator().evaluate(
            _ctx("not json at all", assertion_type=AssertionType.JSON_VALID)
        )
        assert result.passed is False

    def test_json_in_code_block(self) -> None:
        output = '```json\n{"key": "value"}\n```'
        result = JsonValidEvaluator().evaluate(
            _ctx(output, assertion_type=AssertionType.JSON_VALID)
        )
        assert result.passed is True

    def test_json_key_check(self) -> None:
        result = JsonValidEvaluator().evaluate(
            _ctx('{"name": "Alice"}', "name", assertion_type=AssertionType.JSON_VALID)
        )
        assert result.passed is True

    def test_json_missing_key(self) -> None:
        result = JsonValidEvaluator().evaluate(
            _ctx('{"name": "Alice"}', "age", assertion_type=AssertionType.JSON_VALID)
        )
        assert result.passed is False


class TestSimilarityEvaluator:
    """Tests for similarity evaluator."""

    def test_identical_strings(self) -> None:
        result = SimilarityEvaluator().evaluate(
            _ctx(
                "hello world",
                "hello world",
                threshold=0.9,
                assertion_type=AssertionType.SIMILARITY,
            )
        )
        assert result.passed is True
        assert result.score is not None
        assert result.score >= 0.99

    def test_similar_strings(self) -> None:
        result = SimilarityEvaluator().evaluate(
            _ctx(
                "The capital of France is Paris",
                "Paris is the capital of France",
                threshold=0.5,
                assertion_type=AssertionType.SIMILARITY,
            )
        )
        assert result.passed is True

    def test_dissimilar_strings(self) -> None:
        result = SimilarityEvaluator().evaluate(
            _ctx(
                "apple banana cherry",
                "xyz 123 !!!",
                threshold=0.8,
                assertion_type=AssertionType.SIMILARITY,
            )
        )
        assert result.passed is False

    def test_default_threshold(self) -> None:
        result = SimilarityEvaluator().evaluate(
            _ctx("hello", "hello", assertion_type=AssertionType.SIMILARITY)
        )
        assert result.passed is True


class TestCostEvaluator:
    """Tests for cost evaluator."""

    def test_within_limit(self) -> None:
        result = CostEvaluator().evaluate(
            _ctx("100", max_tokens=500, assertion_type=AssertionType.COST)
        )
        assert result.passed is True

    def test_exceeds_limit(self) -> None:
        result = CostEvaluator().evaluate(
            _ctx("600", max_tokens=500, assertion_type=AssertionType.COST)
        )
        assert result.passed is False

    def test_invalid_token_count(self) -> None:
        result = CostEvaluator().evaluate(
            _ctx("not a number", max_tokens=500, assertion_type=AssertionType.COST)
        )
        assert result.passed is True  # Gracefully skip


class TestLlmJudgeEvaluator:
    """Tests for LLM-as-Judge evaluator."""

    def test_build_judge_prompt(self) -> None:
        judge = LlmJudgeEvaluator()
        ctx = _ctx(
            "The answer is 42",
            "Must be accurate",
            assertion_type=AssertionType.LLM_JUDGE,
        )
        ctx.prompt_rendered = "What is the answer?"
        prompt = judge.build_judge_prompt(ctx)
        assert "What is the answer?" in prompt
        assert "The answer is 42" in prompt
        assert "Must be accurate" in prompt

    def test_parse_pass_response(self) -> None:
        judge = LlmJudgeEvaluator()
        result = judge.parse_judge_response("PASS - the answer is correct")
        assert result.passed is True

    def test_parse_fail_response(self) -> None:
        judge = LlmJudgeEvaluator()
        result = judge.parse_judge_response("FAIL - the answer is wrong")
        assert result.passed is False

    def test_parse_ambiguous_response(self) -> None:
        judge = LlmJudgeEvaluator()
        result = judge.parse_judge_response("The answer seems partially correct")
        assert result.passed is False  # Not starting with PASS


class TestEvaluatorRegistry:
    """Tests for evaluator registry."""

    @pytest.mark.parametrize("assertion_type", list(AssertionType))
    def test_all_types_registered(self, assertion_type: AssertionType) -> None:
        """Test that all assertion types have registered evaluators."""
        evaluator = create_evaluator(assertion_type)
        assert evaluator is not None

    def test_creates_correct_type(self) -> None:
        assert isinstance(create_evaluator(AssertionType.EXACT), ExactEvaluator)
        assert isinstance(create_evaluator(AssertionType.CONTAINS), ContainsEvaluator)
        assert isinstance(create_evaluator(AssertionType.REGEX), RegexEvaluator)
        assert isinstance(
            create_evaluator(AssertionType.JSON_VALID), JsonValidEvaluator
        )
        assert isinstance(
            create_evaluator(AssertionType.SIMILARITY), SimilarityEvaluator
        )
        assert isinstance(create_evaluator(AssertionType.LLM_JUDGE), LlmJudgeEvaluator)
        assert isinstance(create_evaluator(AssertionType.COST), CostEvaluator)
