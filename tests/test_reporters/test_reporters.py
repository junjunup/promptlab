"""Tests for reporters."""

from __future__ import annotations

from pathlib import Path

import pytest

from promptlab.reporters.csv_reporter import CsvReporter
from promptlab.reporters.json_reporter import JsonReporter


@pytest.fixture
def sample_results() -> dict:
    """Sample evaluation results for testing reporters."""
    return {
        "run_id": "test123",
        "description": "Test run",
        "timestamp": 1711526400.0,
        "total_tests": 2,
        "total_passed": 1,
        "total_failed": 1,
        "overall_pass_rate": 0.5,
        "total_cost_usd": 0.002,
        "total_duration_ms": 1500.0,
        "results": [
            {
                "test_index": 0,
                "test_description": "Test 1",
                "provider_id": "gpt4",
                "prompt_id": "v1",
                "output": "Paris",
                "passed": True,
                "latency_ms": 500.0,
                "token_usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 5,
                    "total_tokens": 15,
                    "estimated_cost_usd": 0.001,
                },
                "assertions": [
                    {"type": "contains", "passed": True, "expected": "Paris"},
                ],
                "error": None,
            },
            {
                "test_index": 1,
                "test_description": "Test 2",
                "provider_id": "gpt4",
                "prompt_id": "v1",
                "output": "London",
                "passed": False,
                "latency_ms": 600.0,
                "token_usage": {
                    "prompt_tokens": 12,
                    "completion_tokens": 6,
                    "total_tokens": 18,
                    "estimated_cost_usd": 0.001,
                },
                "assertions": [
                    {"type": "contains", "passed": False, "expected": "Berlin"},
                ],
                "error": None,
            },
        ],
        "provider_summaries": [
            {
                "provider_id": "gpt4",
                "total_tests": 2,
                "passed": 1,
                "failed": 1,
                "pass_rate": 0.5,
                "total_tokens": 33,
                "total_cost_usd": 0.002,
                "avg_latency_ms": 550.0,
            },
        ],
    }


class TestJsonReporter:
    """Tests for JSON reporter."""

    def test_save_creates_file(self, tmp_path: Path, sample_results: dict) -> None:
        """Test that save creates a JSON file."""
        output = str(tmp_path / "results.json")
        saved = JsonReporter().save(sample_results, output)
        assert Path(saved).exists()

    def test_save_valid_json(self, tmp_path: Path, sample_results: dict) -> None:
        """Test that saved file is valid JSON."""
        import json

        output = str(tmp_path / "results.json")
        JsonReporter().save(sample_results, output)

        with open(output) as f:
            data = json.load(f)

        assert data["run_id"] == "test123"
        assert data["total_tests"] == 2

    def test_save_creates_parent_dirs(
        self, tmp_path: Path, sample_results: dict
    ) -> None:
        """Test that save creates parent directories."""
        output = str(tmp_path / "nested" / "dir" / "results.json")
        saved = JsonReporter().save(sample_results, output)
        assert Path(saved).exists()


class TestCsvReporter:
    """Tests for CSV reporter."""

    def test_save_creates_file(self, tmp_path: Path, sample_results: dict) -> None:
        """Test that save creates a CSV file."""
        output = str(tmp_path / "results.csv")
        saved = CsvReporter().save(sample_results, output)
        assert Path(saved).exists()

    def test_save_correct_rows(self, tmp_path: Path, sample_results: dict) -> None:
        """Test that CSV has correct number of rows."""
        import csv

        output = str(tmp_path / "results.csv")
        CsvReporter().save(sample_results, output)

        with open(output) as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2
        assert rows[0]["provider_id"] == "gpt4"
        assert rows[0]["passed"] == "True"
        assert rows[1]["passed"] == "False"

    def test_save_empty_results(self, tmp_path: Path) -> None:
        """Test saving empty results."""
        output = str(tmp_path / "empty.csv")
        CsvReporter().save({"results": []}, output)
        assert Path(output).exists()
