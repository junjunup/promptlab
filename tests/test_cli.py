"""Tests for CLI commands."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from promptlab.cli import app

runner = CliRunner()


class TestVersionCommand:
    """Tests for the version command."""

    def test_version_output(self) -> None:
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "PromptLab" in result.output
        assert "0.1.0" in result.output


class TestInitCommand:
    """Tests for the init command."""

    def test_init_creates_file(self, tmp_path: Path) -> None:
        output = str(tmp_path / "eval.yaml")
        result = runner.invoke(app, ["init", "--output", output])
        assert result.exit_code == 0
        assert Path(output).exists()
        assert "providers" in Path(output).read_text()

    def test_init_default_filename(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["init"])
        assert result.exit_code == 0
        assert (tmp_path / "eval.yaml").exists()


class TestRunCommand:
    """Tests for the run command."""

    def test_run_missing_file(self) -> None:
        result = runner.invoke(app, ["run", "nonexistent.yaml"])
        assert result.exit_code == 1
        assert "not found" in result.output.lower() or "error" in result.output.lower()

    def test_run_invalid_provider_filter(self, tmp_path: Path) -> None:
        config = tmp_path / "eval.yaml"
        config.write_text("""\
providers:
  - id: test
    type: openai
    model: gpt-4o-mini
prompts:
  - id: v1
    content: "test"
tests:
  - vars: {}
    assert:
      - type: contains
        value: "test"
""")
        result = runner.invoke(app, ["run", str(config), "--provider", "nonexistent"])
        assert result.exit_code == 1
