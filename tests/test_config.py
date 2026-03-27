"""Tests for config loading and validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from promptlab.config import _resolve_env_vars, generate_example_config, load_config
from promptlab.exceptions import ConfigError
from promptlab.models import EvalConfig


class TestLoadConfig:
    """Test YAML config loading."""

    def test_load_valid_config(self, tmp_path: Path, sample_yaml_content: str) -> None:
        """Test loading a valid YAML config file."""
        config_file = tmp_path / "eval.yaml"
        config_file.write_text(sample_yaml_content)

        config = load_config(str(config_file))

        assert isinstance(config, EvalConfig)
        assert config.description == "Test config"
        assert len(config.providers) == 1
        assert len(config.prompts) == 1
        assert len(config.tests) == 1

    def test_load_nonexistent_file(self) -> None:
        """Test loading a file that doesn't exist."""
        with pytest.raises(ConfigError, match="not found"):
            load_config("nonexistent.yaml")

    def test_load_wrong_extension(self, tmp_path: Path) -> None:
        """Test loading a file with wrong extension."""
        config_file = tmp_path / "eval.json"
        config_file.write_text("{}")

        with pytest.raises(ConfigError, match=r"must be .yaml"):
            load_config(str(config_file))

    def test_load_invalid_yaml(self, tmp_path: Path) -> None:
        """Test loading invalid YAML content."""
        config_file = tmp_path / "eval.yaml"
        config_file.write_text(":\n  invalid: [yaml: broken")

        with pytest.raises(ConfigError, match="Invalid YAML"):
            load_config(str(config_file))

    def test_load_non_dict_yaml(self, tmp_path: Path) -> None:
        """Test loading YAML that is not a dict."""
        config_file = tmp_path / "eval.yaml"
        config_file.write_text("- just\n- a\n- list")

        with pytest.raises(ConfigError, match="mapping"):
            load_config(str(config_file))

    def test_load_empty_providers(self, tmp_path: Path) -> None:
        """Test config with no providers."""
        config_file = tmp_path / "eval.yaml"
        config_file.write_text("""\
providers: []
prompts:
  - id: v1
    content: "test"
tests:
  - vars: {}
    assert:
      - type: contains
        value: "test"
""")
        with pytest.raises(ConfigError, match="provider"):
            load_config(str(config_file))

    def test_load_duplicate_provider_ids(self, tmp_path: Path) -> None:
        """Test config with duplicate provider IDs."""
        config_file = tmp_path / "eval.yaml"
        config_file.write_text("""\
providers:
  - id: same
    type: openai
    model: gpt-4o-mini
  - id: same
    type: openai
    model: gpt-4o
prompts:
  - id: v1
    content: "test"
tests:
  - vars: {}
    assert:
      - type: contains
        value: "test"
""")
        with pytest.raises(ConfigError, match="Duplicate provider"):
            load_config(str(config_file))

    def test_load_with_yml_extension(
        self, tmp_path: Path, sample_yaml_content: str
    ) -> None:
        """Test loading a .yml file."""
        config_file = tmp_path / "eval.yml"
        config_file.write_text(sample_yaml_content)

        config = load_config(str(config_file))
        assert isinstance(config, EvalConfig)

    def test_settings_override(self, tmp_path: Path, sample_yaml_content: str) -> None:
        """Test overriding settings."""
        config_file = tmp_path / "eval.yaml"
        config_file.write_text(sample_yaml_content)

        config = load_config(str(config_file), concurrency=10)
        assert config.settings.concurrency == 10


class TestResolveEnvVars:
    """Test environment variable resolution."""

    def test_resolve_simple_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test resolving a simple env var."""
        monkeypatch.setenv("TEST_KEY", "secret123")
        result = _resolve_env_vars("${TEST_KEY}")
        assert result == "secret123"

    def test_resolve_missing_var(self) -> None:
        """Test resolving a missing env var raises error."""
        with pytest.raises(ConfigError, match="not set"):
            _resolve_env_vars("${DEFINITELY_NOT_SET_12345}")

    def test_resolve_nested_dict(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test resolving env vars in nested dict."""
        monkeypatch.setenv("API_KEY", "key123")
        data = {"provider": {"api_key": "${API_KEY}", "model": "gpt-4"}}
        result = _resolve_env_vars(data)
        assert result["provider"]["api_key"] == "key123"
        assert result["provider"]["model"] == "gpt-4"

    def test_resolve_in_list(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test resolving env vars in list."""
        monkeypatch.setenv("ITEM", "hello")
        result = _resolve_env_vars(["${ITEM}", "world"])
        assert result == ["hello", "world"]

    def test_non_env_string_unchanged(self) -> None:
        """Test that normal strings are not modified."""
        result = _resolve_env_vars("just a normal string")
        assert result == "just a normal string"

    def test_non_string_values_unchanged(self) -> None:
        """Test that non-string values pass through."""
        assert _resolve_env_vars(42) == 42
        assert _resolve_env_vars(True) is True
        assert _resolve_env_vars(None) is None


class TestGenerateExampleConfig:
    """Test example config generation."""

    def test_generates_valid_yaml(self) -> None:
        """Test that the generated example is valid YAML."""
        import yaml

        content = generate_example_config()
        data = yaml.safe_load(content)
        assert isinstance(data, dict)
        assert "providers" in data
        assert "prompts" in data
        assert "tests" in data

    def test_example_is_loadable(self, tmp_path: Path) -> None:
        """Test that the generated example can be loaded as config."""
        config_file = tmp_path / "example.yaml"
        config_file.write_text(generate_example_config())
        config = load_config(str(config_file))
        assert isinstance(config, EvalConfig)
